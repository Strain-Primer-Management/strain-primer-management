"""Tests for the strain pages: login, permissions, content, validation and audit fields."""

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.mixins import PAGE_SIZE
from apps.core.tests.helpers import make_user, stub_templates
from apps.plasmids.models import Plasmid
from apps.strains.forms import CULTURING_TEMP_MAX, CULTURING_TEMP_MIN
from apps.strains.models import Strain, StrainPlasmid

# Tiny stand-ins for the frontend templates: they print what the real pages will receive.
STUBS = {
    "strains/strain_list.html": (
        "{% for s in object_list %}ROW {{ s.strain_id }} {{ s.host_organism }} {{ s.genotype }}"
        " {{ s.culturing_temp }} {{ s.culturing_medium }} {{ s.freezer_location }};{% endfor %}"
        "PAGE {{ page_obj.number }} PAGINATED {{ is_paginated }}"
    ),
    "strains/strain_detail.html": (
        "STRAIN {{ object.strain_id }} {{ object.biosafety_level }}"
        "{% for l in plasmid_links %} PLASMID {{ l.plasmid }} {{ l.notes }}{% endfor %}"
        "{% if parent %} PARENT {{ parent }}{% endif %}"
        "{% for c in children %} CHILD {{ c }}{% endfor %}"
        "{% for m in messages %} MSG {{ m }}{% endfor %}"
    ),
    "strains/strain_form.html": (
        "FORM {{ form.as_p }}"
        "{% for s in form.biosafety_suggestions %} SUGGEST {{ s }}{% endfor %}"
        "{% if object %} EDITING {{ object.strain_id }}{% endif %}"
    ),
}


@stub_templates(STUBS)
class StrainViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)
        cls.student = make_user("Student")
        cls.staff = make_user("Staff")
        cls.strain = Strain.objects.create(
            strain_id="Example-900",
            host_organism="E. coli K-12",
            genotype="recA1, endA1",
            culturing_temp="37.0",
            culturing_medium="LB",
            freezer_location="Freezer 2",
            biosafety_level="BSL-1",
        )

    def post_new(self, **changes):
        data = {"strain_id": "Example-901", "culturing_temp": "30.5", "host_organism": "Yeast"}
        return self.client.post(reverse("strains:create"), {**data, **changes})

    def urls(self):
        return [
            ("strains:list", []),
            ("strains:detail", [self.strain.pk]),
            ("strains:create", []),
            ("strains:update", [self.strain.pk]),
        ]

    # --- login and permissions -----------------------------------------------------------
    def test_anonymous_is_sent_to_login(self):
        for name, args in self.urls():
            url = reverse(name, args=args)
            self.assertRedirects(self.client.get(url), f"{reverse('accounts:login')}?next={url}")

    def test_user_without_any_permission_gets_403_everywhere(self):
        nobody = make_user("Student", "nobody")
        nobody.groups.clear()
        self.client.force_login(nobody)
        for name, args in self.urls():
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 403, name)

    def test_student_can_look_but_not_add_or_change(self):
        self.client.force_login(self.student)
        for name, args in self.urls()[:2]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200, name)
        for name, args in self.urls()[2:]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 403, name)
        self.assertEqual(self.post_new().status_code, 403)
        self.assertFalse(Strain.objects.filter(strain_id="Example-901").exists())

    # --- list ------------------------------------------------------------------------------
    def test_list_shows_the_strain_fields(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("strains:list"))
        self.assertContains(response, "ROW Example-900 E. coli K-12 recA1, endA1 37.0 LB Freezer 2")
        self.assertContains(response, "PAGINATED False")

    def test_list_is_newest_first_and_has_25_per_page(self):
        for number in range(PAGE_SIZE):
            Strain.objects.create(strain_id=f"Q-{number:03d}")
        self.client.force_login(self.student)
        first = self.client.get(reverse("strains:list"))
        self.assertEqual(len(first.context["object_list"]), PAGE_SIZE)
        self.assertEqual(first.context["object_list"][0].strain_id, f"Q-{PAGE_SIZE - 1:03d}")
        second = self.client.get(reverse("strains:list") + "?page=2")
        self.assertEqual([s.strain_id for s in second.context["object_list"]], ["Example-900"])

    # --- detail ----------------------------------------------------------------------------
    def test_a_strain_without_plasmids_or_parent_shows_fine(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("strains:detail", args=[self.strain.pk]))
        self.assertContains(response, "STRAIN Example-900 BSL-1")
        self.assertEqual(list(response.context["plasmid_links"]), [])
        self.assertIsNone(response.context["parent"])
        self.assertEqual(list(response.context["children"]), [])

    def test_detail_shows_plasmids_parent_and_children(self):
        parent = Strain.objects.create(strain_id="Example-800")
        Strain.objects.filter(pk=self.strain.pk).update(parent_strain=parent)
        Strain.objects.create(strain_id="Example-950", parent_strain=self.strain)
        plasmid = Plasmid.objects.create(plasmid_name="pEX-900")
        StrainPlasmid.objects.create(strain=self.strain, plasmid=plasmid, notes="from freezer")
        self.client.force_login(self.student)
        response = self.client.get(reverse("strains:detail", args=[self.strain.pk]))
        self.assertContains(response, "PLASMID pEX-900 from freezer")
        self.assertContains(response, "PARENT Example-800")
        self.assertContains(response, "CHILD Example-950")

    # --- create ----------------------------------------------------------------------------
    def test_staff_sees_the_empty_form_with_suggestions(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("strains:create"))
        self.assertContains(response, "SUGGEST BSL-1")
        self.assertContains(response, 'list="strain-biosafety-options"')
        self.assertNotIn("object", response.context)

    def test_create_saves_and_sets_the_audit_fields(self):
        self.client.force_login(self.staff)
        response = self.post_new()
        strain = Strain.objects.get(strain_id="Example-901")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("strains:detail", args=[strain.pk]))
        self.assertEqual(str(strain.culturing_temp), "30.5")
        self.assertEqual(strain.created_by, self.staff)
        self.assertEqual(strain.updated_by, self.staff)
        self.assertContains(self.client.get(response.url), "MSG Strain Example-901 was created.")

    def test_a_strain_with_only_an_id_saves_fine(self):
        self.client.force_login(self.staff)
        response = self.post_new(culturing_temp="", host_organism="")
        self.assertEqual(response.status_code, 302)
        strain = Strain.objects.get(strain_id="Example-901")
        self.assertIsNone(strain.culturing_temp)
        self.assertIsNone(strain.parent_strain)

    def test_create_needs_a_strain_id(self):
        self.client.force_login(self.staff)
        response = self.post_new(strain_id="")
        self.assertEqual(set(response.context["form"].errors), {"strain_id"})

    def test_temperature_must_be_a_number_in_range(self):
        self.client.force_login(self.staff)
        too_cold = str(CULTURING_TEMP_MIN - 1)
        too_hot = str(CULTURING_TEMP_MAX + 1)
        for bad in [too_cold, too_hot, "warm", "37.55"]:
            response = self.post_new(culturing_temp=bad)
            self.assertIn("culturing_temp", response.context["form"].errors, bad)
        self.assertFalse(Strain.objects.filter(strain_id="Example-901").exists())

    def test_create_rejects_a_duplicate_id_in_any_capitalisation(self):
        self.client.force_login(self.staff)
        response = self.post_new(strain_id="example-900")
        self.assertEqual(response.status_code, 200)
        self.assertIn("already exists", " ".join(response.context["form"].non_field_errors()))
        self.assertEqual(Strain.objects.filter(strain_id__iexact="example-900").count(), 1)

    def test_other_biosafety_text_is_accepted(self):
        self.client.force_login(self.staff)
        self.post_new(biosafety_level="Special")
        self.assertEqual(Strain.objects.get(strain_id="Example-901").biosafety_level, "Special")

    def test_a_parent_can_be_chosen_on_create(self):
        self.client.force_login(self.staff)
        self.post_new(parent_strain=self.strain.pk)
        self.assertEqual(Strain.objects.get(strain_id="Example-901").parent_strain, self.strain)

    # --- update and lineage rules ------------------------------------------------------------
    def update_data(self, **changes):
        return {"strain_id": "Example-900", **changes}

    def test_update_changes_the_strain_and_keeps_created_by(self):
        other = make_user("Staff", "other-staff")
        Strain.objects.filter(pk=self.strain.pk).update(created_by=other)
        self.client.force_login(self.staff)
        url = reverse("strains:update", args=[self.strain.pk])
        self.assertContains(self.client.get(url), "EDITING Example-900")
        response = self.client.post(url, self.update_data(genotype="new genotype"))
        self.assertEqual(response.url, reverse("strains:detail", args=[self.strain.pk]))
        self.strain.refresh_from_db()
        self.assertEqual(self.strain.genotype, "new genotype")
        self.assertEqual(self.strain.created_by, other)
        self.assertEqual(self.strain.updated_by, self.staff)

    def test_the_parent_dropdown_does_not_offer_the_strain_itself(self):
        Strain.objects.create(strain_id="Example-800")
        self.client.force_login(self.staff)
        response = self.client.get(reverse("strains:update", args=[self.strain.pk]))
        offered = [s.strain_id for s in response.context["form"].fields["parent_strain"].queryset]
        self.assertEqual(offered, ["Example-800"])

    def test_a_strain_cannot_be_its_own_parent(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("strains:update", args=[self.strain.pk]),
            self.update_data(parent_strain=self.strain.pk),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("parent_strain", response.context["form"].errors)

    def test_a_loop_of_parents_is_rejected(self):
        child = Strain.objects.create(strain_id="Example-910", parent_strain=self.strain)
        grandchild = Strain.objects.create(strain_id="Example-920", parent_strain=child)
        self.client.force_login(self.staff)
        for descendant in (child, grandchild):
            response = self.client.post(
                reverse("strains:update", args=[self.strain.pk]),
                self.update_data(parent_strain=descendant.pk),
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("loop", " ".join(response.context["form"].errors["parent_strain"]))
        self.strain.refresh_from_db()
        self.assertIsNone(self.strain.parent_strain)

    def test_update_may_keep_its_own_id_and_set_a_valid_parent(self):
        parent = Strain.objects.create(strain_id="Example-800")
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("strains:update", args=[self.strain.pk]),
            {"strain_id": "EXAMPLE-900", "parent_strain": parent.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.strain.refresh_from_db()
        self.assertEqual(self.strain.parent_strain, parent)
