"""Tests for the plasmid pages: login, permissions, content, validation and audit fields."""

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.mixins import PAGE_SIZE
from apps.core.tests.helpers import make_user, stub_templates
from apps.plasmids.models import Plasmid, PlasmidPrimerLink
from apps.primers.models import Primer
from apps.strains.models import Strain, StrainPlasmid

# Tiny stand-ins for the frontend templates: they print what the real pages will receive.
STUBS = {
    "plasmids/plasmid_list.html": (
        "{% for p in object_list %}ROW {{ p.plasmid_name }} {{ p.size_bp }}"
        " {{ p.resistance_markers }} {{ p.get_copy_number_display }};{% endfor %}"
        "PAGE {{ page_obj.number }} PAGINATED {{ is_paginated }}"
    ),
    "plasmids/plasmid_detail.html": (
        "PLASMID {{ object.plasmid_name }} {{ object.description }}"
        "{% for l in primer_links %} PRIMER {{ l.primer }} {{ l.orientation }}"
        " {{ l.binding_position }}{% endfor %}"
        "{% for s in strains %} STRAIN {{ s }}{% endfor %}"
        "{% for m in messages %} MSG {{ m }}{% endfor %}"
    ),
    "plasmids/plasmid_form.html": (
        "FORM {{ form.as_p }}{% if object %} EDITING {{ object.plasmid_name }}{% endif %}"
    ),
}


@stub_templates(STUBS)
class PlasmidViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)
        cls.student = make_user("Student")
        cls.staff = make_user("Staff")
        cls.plasmid = Plasmid.objects.create(
            plasmid_name="pEX-900",
            size_bp=3000,
            resistance_markers="Ampicillin",
            copy_number="high",
            description="A test plasmid",
        )

    def post_new(self, **changes):
        data = {"plasmid_name": "pEX-901", "size_bp": "4000", "copy_number": "low"}
        return self.client.post(reverse("plasmids:create"), {**data, **changes})

    def urls(self):
        return [
            ("plasmids:list", []),
            ("plasmids:detail", [self.plasmid.pk]),
            ("plasmids:create", []),
            ("plasmids:update", [self.plasmid.pk]),
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
        self.assertFalse(Plasmid.objects.filter(plasmid_name="pEX-901").exists())

    # --- list ------------------------------------------------------------------------------
    def test_list_shows_the_plasmid_fields(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("plasmids:list"))
        self.assertContains(response, "ROW pEX-900 3000 Ampicillin High")
        self.assertContains(response, "PAGINATED False")

    def test_list_is_newest_first_and_has_25_per_page(self):
        for number in range(PAGE_SIZE):
            Plasmid.objects.create(plasmid_name=f"pQ-{number:03d}")
        self.client.force_login(self.student)
        first = self.client.get(reverse("plasmids:list"))
        self.assertEqual(len(first.context["object_list"]), PAGE_SIZE)
        self.assertEqual(first.context["object_list"][0].plasmid_name, f"pQ-{PAGE_SIZE - 1:03d}")
        second = self.client.get(reverse("plasmids:list") + "?page=2")
        self.assertEqual([p.plasmid_name for p in second.context["object_list"]], ["pEX-900"])

    # --- detail ----------------------------------------------------------------------------
    def test_detail_without_links_works(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("plasmids:detail", args=[self.plasmid.pk]))
        self.assertContains(response, "PLASMID pEX-900 A test plasmid")
        self.assertEqual(list(response.context["primer_links"]), [])
        self.assertEqual(list(response.context["strains"]), [])

    def test_detail_lists_linked_primers_and_strains(self):
        primer = Primer.objects.create(primer_id="P-900", sequence="ATGC")
        PlasmidPrimerLink.objects.create(
            plasmid=self.plasmid, primer=primer, orientation="reverse", binding_position="5-25"
        )
        strain = Strain.objects.create(strain_id="Example-900")
        StrainPlasmid.objects.create(strain=strain, plasmid=self.plasmid)
        self.client.force_login(self.student)
        response = self.client.get(reverse("plasmids:detail", args=[self.plasmid.pk]))
        self.assertContains(response, "PRIMER P-900 reverse 5-25")
        self.assertContains(response, "STRAIN Example-900")

    # --- create ----------------------------------------------------------------------------
    def test_staff_sees_the_empty_form(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("plasmids:create"))
        self.assertContains(response, 'name="plasmid_name"')
        self.assertContains(response, 'name="copy_number"')
        self.assertNotIn("object", response.context)

    def test_create_saves_and_sets_the_audit_fields(self):
        self.client.force_login(self.staff)
        response = self.post_new()
        plasmid = Plasmid.objects.get(plasmid_name="pEX-901")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("plasmids:detail", args=[plasmid.pk]))
        self.assertEqual((plasmid.size_bp, plasmid.copy_number), (4000, "low"))
        self.assertEqual(plasmid.created_by, self.staff)
        self.assertEqual(plasmid.updated_by, self.staff)
        self.assertContains(self.client.get(response.url), "MSG Plasmid pEX-901 was created.")

    def test_a_plasmid_with_only_a_name_saves_fine(self):
        self.client.force_login(self.staff)
        response = self.post_new(size_bp="", copy_number="")
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(Plasmid.objects.get(plasmid_name="pEX-901").size_bp)

    def test_create_needs_a_name(self):
        self.client.force_login(self.staff)
        response = self.post_new(plasmid_name="")
        self.assertEqual(set(response.context["form"].errors), {"plasmid_name"})

    def test_size_must_be_a_positive_whole_number(self):
        self.client.force_login(self.staff)
        for bad in ["0", "-5", "2.5", "abc"]:
            response = self.post_new(size_bp=bad)
            self.assertIn("size_bp", response.context["form"].errors, bad)
        self.assertFalse(Plasmid.objects.filter(plasmid_name="pEX-901").exists())

    def test_copy_number_must_be_one_of_the_choices(self):
        self.client.force_login(self.staff)
        response = self.post_new(copy_number="huge")
        self.assertIn("copy_number", response.context["form"].errors)

    def test_create_rejects_a_duplicate_name_in_any_capitalisation(self):
        self.client.force_login(self.staff)
        response = self.post_new(plasmid_name="PEX-900")
        self.assertEqual(response.status_code, 200)
        self.assertIn("already exists", " ".join(response.context["form"].non_field_errors()))
        self.assertEqual(Plasmid.objects.filter(plasmid_name__iexact="pex-900").count(), 1)

    # --- update ----------------------------------------------------------------------------
    def test_update_changes_the_plasmid_and_keeps_created_by(self):
        other = make_user("Staff", "other-staff")
        Plasmid.objects.filter(pk=self.plasmid.pk).update(created_by=other)
        self.client.force_login(self.staff)
        url = reverse("plasmids:update", args=[self.plasmid.pk])
        self.assertContains(self.client.get(url), "EDITING pEX-900")
        response = self.client.post(url, {"plasmid_name": "pEX-900", "size_bp": "3500"})
        self.assertEqual(response.url, reverse("plasmids:detail", args=[self.plasmid.pk]))
        self.plasmid.refresh_from_db()
        self.assertEqual(self.plasmid.size_bp, 3500)
        self.assertEqual(self.plasmid.created_by, other)
        self.assertEqual(self.plasmid.updated_by, self.staff)

    def test_update_may_keep_its_own_name(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("plasmids:update", args=[self.plasmid.pk]), {"plasmid_name": "pex-900"}
        )
        self.assertEqual(response.status_code, 302)
