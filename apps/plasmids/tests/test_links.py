"""Tests for linking primers to a plasmid and unlinking them again."""

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.tests.helpers import make_user, stub_templates
from apps.plasmids.models import Plasmid, PlasmidPrimerLink
from apps.primers.models import Primer

STUBS = {
    "plasmids/plasmid_detail.html": (
        "PLASMID {{ object.plasmid_name }}"
        "{% for l in primer_links %} LINK{{ l.pk }} {{ l.primer }} {{ l.orientation }}"
        " {{ l.binding_position }} {{ l.notes }}{% endfor %}"
        "{% if link_form %} FORMFIELDS {{ link_form.as_p }} ERRORS {{ link_form.non_field_errors }}"
        "{% else %} NOFORM{% endif %}"
        "{% for m in messages %} MSG {{ m }}{% endfor %}"
    ),
}


@stub_templates(STUBS)
class PlasmidLinkTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)
        cls.student = make_user("Student")
        cls.staff = make_user("Staff")
        cls.plasmid = Plasmid.objects.create(plasmid_name="pEX-700")
        cls.primer = Primer.objects.create(primer_id="P-700", sequence="ATGC")
        cls.link_url = reverse("plasmids:link_primer", args=[cls.plasmid.pk])

    def data(self, **changes):
        base = {"primer": self.primer.pk, "orientation": "forward", "binding_position": "10-30"}
        return {**base, **changes}

    def unlink_url(self, link):
        return reverse("plasmids:unlink_primer", args=[self.plasmid.pk, link.pk])

    def test_detail_works_for_a_plasmid_with_no_links_and_shows_the_form_to_staff_only(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("plasmids:detail", args=[self.plasmid.pk]))
        self.assertContains(response, 'name="binding_position"')
        self.client.force_login(self.student)
        response = self.client.get(reverse("plasmids:detail", args=[self.plasmid.pk]))
        self.assertContains(response, "NOFORM")
        self.assertIsNone(response.context["link_form"])

    def test_anonymous_is_sent_to_login(self):
        response = self.client.post(self.link_url, self.data())
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
        self.assertFalse(PlasmidPrimerLink.objects.exists())

    def test_student_cannot_link_or_unlink(self):
        link = PlasmidPrimerLink.objects.create(plasmid=self.plasmid, primer=self.primer)
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(self.link_url, self.data()).status_code, 403)
        self.assertEqual(self.client.post(self.unlink_url(link)).status_code, 403)
        self.assertTrue(PlasmidPrimerLink.objects.filter(pk=link.pk).exists())

    def test_staff_links_a_primer_with_orientation_position_and_audit_fields(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.link_url, self.data(notes="works well"))
        self.assertEqual(response.url, reverse("plasmids:detail", args=[self.plasmid.pk]))
        link = PlasmidPrimerLink.objects.get()
        self.assertEqual((link.orientation, link.binding_position), ("forward", "10-30"))
        self.assertEqual((link.created_by, link.updated_by), (self.staff, self.staff))
        page = self.client.get(response.url)
        self.assertContains(page, "LINK%d P-700 forward 10-30 works well" % link.pk)
        self.assertContains(page, "MSG Primer P-700 was linked to pEX-700.")

    def test_a_link_needs_only_the_primer(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.link_url, {"primer": self.primer.pk})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PlasmidPrimerLink.objects.get().orientation, "")

    def test_linking_the_exact_same_link_twice_shows_a_friendly_error(self):
        PlasmidPrimerLink.objects.create(
            plasmid=self.plasmid,
            primer=self.primer,
            orientation="forward",
            binding_position="10-30",
        )
        self.client.force_login(self.staff)
        response = self.client.post(self.link_url, self.data())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This exact plasmid-primer link already exists.")
        self.assertEqual(PlasmidPrimerLink.objects.count(), 1)

    def test_the_same_primer_may_bind_at_another_position(self):
        PlasmidPrimerLink.objects.create(
            plasmid=self.plasmid,
            primer=self.primer,
            orientation="forward",
            binding_position="10-30",
        )
        self.client.force_login(self.staff)
        response = self.client.post(self.link_url, self.data(binding_position="500-520"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PlasmidPrimerLink.objects.count(), 2)

    def test_a_bad_orientation_or_unknown_primer_is_a_form_error_not_a_crash(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.link_url, self.data(orientation="sideways"))
        self.assertIn("orientation", response.context["link_form"].errors)
        response = self.client.post(self.link_url, self.data(primer=999999))
        self.assertIn("primer", response.context["link_form"].errors)

    def test_the_link_urls_accept_post_only(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.link_url).status_code, 405)

    def test_unlinking_keeps_both_records(self):
        link = PlasmidPrimerLink.objects.create(plasmid=self.plasmid, primer=self.primer)
        self.client.force_login(self.staff)
        response = self.client.post(self.unlink_url(link))
        self.assertEqual(response.url, reverse("plasmids:detail", args=[self.plasmid.pk]))
        self.assertFalse(PlasmidPrimerLink.objects.exists())
        self.assertTrue(Plasmid.objects.filter(pk=self.plasmid.pk).exists())
        self.assertTrue(Primer.objects.filter(pk=self.primer.pk).exists())
        self.assertContains(self.client.get(response.url), "MSG Primer P-700 is no longer linked")

    def test_unlink_with_the_wrong_plasmid_is_a_404_and_deletes_nothing(self):
        other = Plasmid.objects.create(plasmid_name="pEX-701")
        link = PlasmidPrimerLink.objects.create(plasmid=other, primer=self.primer)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(self.unlink_url(link)).status_code, 404)
        self.assertTrue(PlasmidPrimerLink.objects.filter(pk=link.pk).exists())

    def test_get_on_unlink_is_not_allowed(self):
        link = PlasmidPrimerLink.objects.create(plasmid=self.plasmid, primer=self.primer)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.unlink_url(link)).status_code, 405)
        self.assertTrue(PlasmidPrimerLink.objects.filter(pk=link.pk).exists())
