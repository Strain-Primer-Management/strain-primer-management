"""Tests for the primer pages: login, permissions, content, validation and audit fields."""

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.mixins import PAGE_SIZE
from apps.core.tests.helpers import make_user, stub_templates
from apps.plasmids.models import Plasmid, PlasmidPrimerLink
from apps.primers.models import Primer

# Tiny stand-ins for the frontend templates: they print what the real pages will receive.
STUBS = {
    "primers/primer_list.html": (
        "{% for p in object_list %}ROW {{ p.primer_id }} {{ p.sequence }} {{ p.length_bp }}"
        " {{ p.melting_temp_tm }} {{ p.purpose }} {{ p.freezer_location }};{% endfor %}"
        "PAGE {{ page_obj.number }} PAGINATED {{ is_paginated }}"
    ),
    "primers/primer_detail.html": (
        "PRIMER {{ object.primer_id }}"
        "{% for l in links %} LINK {{ l.plasmid }} {{ l.orientation }} {{ l.binding_position }}"
        "{% endfor %}"
        "{% for m in messages %} MSG {{ m }}{% endfor %}"
    ),
    "primers/primer_form.html": (
        "FORM {{ form.as_p }} ERRORS {{ form.errors }}"
        "{% for s in form.purpose_suggestions %} SUGGEST {{ s }}{% endfor %}"
        "{% if object %} EDITING {{ object.primer_id }}{% endif %}"
    ),
}


@stub_templates(STUBS)
class PrimerViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)
        cls.student = make_user("Student")
        cls.staff = make_user("Staff")
        cls.primer = Primer.objects.create(
            primer_id="P-900",
            sequence="ATGCTAGCTTGACCGTAC",
            purpose="PCR",
            freezer_location="Box 1",
        )

    def post_new(self, **changes):
        data = {
            "primer_id": "P-901",
            "sequence": "atgc tagc",
            "purpose": "",
            "freezer_location": "",
        }
        return self.client.post(reverse("primers:create"), {**data, **changes})

    # --- login and permissions -----------------------------------------------------------
    def test_anonymous_is_sent_to_login(self):
        for name, args in [
            ("primers:list", []),
            ("primers:detail", [self.primer.pk]),
            ("primers:create", []),
            ("primers:update", [self.primer.pk]),
        ]:
            url = reverse(name, args=args)
            self.assertRedirects(self.client.get(url), f"{reverse('accounts:login')}?next={url}")

    def test_user_without_any_permission_gets_403_everywhere(self):
        nobody = make_user("Student", "nobody")
        nobody.groups.clear()
        self.client.force_login(nobody)
        for name, args in [
            ("primers:list", []),
            ("primers:detail", [self.primer.pk]),
            ("primers:create", []),
            ("primers:update", [self.primer.pk]),
        ]:
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 403, name)

    def test_student_can_look_but_not_add_or_change(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("primers:list")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("primers:detail", args=[self.primer.pk])).status_code, 200
        )
        self.assertEqual(self.client.get(reverse("primers:create")).status_code, 403)
        self.assertEqual(self.post_new().status_code, 403)
        self.assertEqual(
            self.client.get(reverse("primers:update", args=[self.primer.pk])).status_code, 403
        )
        self.assertFalse(Primer.objects.filter(primer_id="P-901").exists())

    # --- list ------------------------------------------------------------------------------
    def test_list_shows_the_primer_fields(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("primers:list"))
        self.assertContains(response, "ROW P-900 ATGCTAGCTTGACCGTAC 18")
        self.assertContains(response, "PCR Box 1")
        self.assertContains(response, str(self.primer.melting_temp_tm))
        self.assertContains(response, "PAGINATED False")

    def test_list_is_newest_first_and_has_25_per_page(self):
        for number in range(PAGE_SIZE):
            Primer.objects.create(primer_id=f"Q-{number:03d}", sequence="ATGC")
        self.client.force_login(self.student)
        first = self.client.get(reverse("primers:list"))
        self.assertEqual(len(first.context["object_list"]), PAGE_SIZE)
        self.assertEqual(first.context["object_list"][0].primer_id, f"Q-{PAGE_SIZE - 1:03d}")
        self.assertTrue(first.context["is_paginated"])
        second = self.client.get(reverse("primers:list") + "?page=2")
        self.assertEqual([p.primer_id for p in second.context["object_list"]], ["P-900"])

    # --- detail ----------------------------------------------------------------------------
    def test_detail_without_links_works(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("primers:detail", args=[self.primer.pk]))
        self.assertContains(response, "PRIMER P-900")
        self.assertEqual(list(response.context["links"]), [])

    def test_detail_lists_the_linked_plasmids(self):
        plasmid = Plasmid.objects.create(plasmid_name="pEX-900")
        PlasmidPrimerLink.objects.create(
            plasmid=plasmid, primer=self.primer, orientation="forward", binding_position="10-30"
        )
        self.client.force_login(self.student)
        response = self.client.get(reverse("primers:detail", args=[self.primer.pk]))
        self.assertContains(response, "LINK pEX-900 forward 10-30")

    # --- create ----------------------------------------------------------------------------
    def test_staff_sees_the_empty_form_with_suggestions(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("primers:create"))
        self.assertContains(response, "SUGGEST Sequencing")
        self.assertContains(response, 'list="primer-purpose-options"')
        self.assertNotIn("object", response.context)

    def test_create_saves_cleans_the_sequence_and_sets_the_audit_fields(self):
        self.client.force_login(self.staff)
        response = self.post_new()
        primer = Primer.objects.get(primer_id="P-901")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("primers:detail", args=[primer.pk]))
        self.assertEqual(primer.sequence, "ATGCTAGC")
        self.assertEqual(primer.length_bp, 8)
        self.assertIsNotNone(primer.melting_temp_tm)
        self.assertEqual(primer.created_by, self.staff)
        self.assertEqual(primer.updated_by, self.staff)
        detail = self.client.get(response.url)
        self.assertContains(detail, "MSG Primer P-901 was created.")

    def test_create_rejects_a_bad_letter(self):
        self.client.force_login(self.staff)
        response = self.post_new(sequence="ATGXZ")
        self.assertEqual(response.status_code, 200)
        self.assertIn("sequence", response.context["form"].errors)
        self.assertFalse(Primer.objects.filter(primer_id="P-901").exists())

    def test_create_needs_primer_id_and_sequence(self):
        self.client.force_login(self.staff)
        response = self.post_new(primer_id="", sequence="")
        self.assertEqual(set(response.context["form"].errors), {"primer_id", "sequence"})

    def test_a_sequence_with_nothing_left_after_cleaning_is_rejected(self):
        self.client.force_login(self.staff)
        response = self.post_new(sequence="5'-  -3'")
        self.assertIn("sequence", response.context["form"].errors)

    def test_create_rejects_a_duplicate_id_in_any_capitalisation(self):
        self.client.force_login(self.staff)
        response = self.post_new(primer_id="p-900")
        self.assertEqual(response.status_code, 200)
        self.assertIn("already exists", " ".join(response.context["form"].non_field_errors()))
        self.assertEqual(Primer.objects.filter(primer_id__iexact="p-900").count(), 1)

    def test_other_purpose_text_is_accepted(self):
        self.client.force_login(self.staff)
        self.post_new(purpose="Something new")
        self.assertEqual(Primer.objects.get(primer_id="P-901").purpose, "Something new")

    # --- update ----------------------------------------------------------------------------
    def test_update_changes_the_primer_and_keeps_created_by(self):
        other = make_user("Staff", "other-staff")
        Primer.objects.filter(pk=self.primer.pk).update(created_by=other)
        self.client.force_login(self.staff)
        url = reverse("primers:update", args=[self.primer.pk])
        self.assertContains(self.client.get(url), "EDITING P-900")
        response = self.client.post(
            url,
            {
                "primer_id": "P-900",
                "sequence": "GGGG",
                "purpose": "Cloning",
                "freezer_location": "",
            },
        )
        self.assertRedirects(response, reverse("primers:detail", args=[self.primer.pk]))
        self.primer.refresh_from_db()
        self.assertEqual(self.primer.sequence, "GGGG")
        self.assertEqual(self.primer.length_bp, 4)
        self.assertEqual(self.primer.created_by, other)
        self.assertEqual(self.primer.updated_by, self.staff)

    def test_update_may_keep_its_own_id(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("primers:update", args=[self.primer.pk]),
            {"primer_id": "p-900", "sequence": "ATGC", "purpose": "", "freezer_location": ""},
        )
        self.assertEqual(response.status_code, 302)
