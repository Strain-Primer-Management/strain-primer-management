"""Tests for linking plasmids to a strain and unlinking them again."""

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.tests.helpers import make_user, stub_templates
from apps.plasmids.models import Plasmid
from apps.strains.models import Strain, StrainPlasmid

STUBS = {
    "strains/strain_detail.html": (
        "STRAIN {{ object.strain_id }}"
        "{% for l in plasmid_links %} LINK{{ l.pk }} {{ l.plasmid }} {{ l.notes }}{% endfor %}"
        "{% if link_form %} FORMFIELDS {{ link_form.as_p }} ERRORS {{ link_form.non_field_errors }}"
        "{% else %} NOFORM{% endif %}"
        "{% for m in messages %} MSG {{ m }}{% endfor %}"
    ),
}


@stub_templates(STUBS)
class StrainLinkTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)
        cls.student = make_user("Student")
        cls.staff = make_user("Staff")
        cls.strain = Strain.objects.create(strain_id="Example-700")
        cls.plasmid = Plasmid.objects.create(plasmid_name="pEX-700")
        cls.link_url = reverse("strains:link_plasmid", args=[cls.strain.pk])

    def unlink_url(self, link):
        return reverse("strains:unlink_plasmid", args=[self.strain.pk, link.pk])

    def test_detail_works_for_a_strain_with_no_links_and_shows_the_form_to_staff_only(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("strains:detail", args=[self.strain.pk]))
        self.assertContains(response, 'name="plasmid"')
        self.client.force_login(self.student)
        response = self.client.get(reverse("strains:detail", args=[self.strain.pk]))
        self.assertContains(response, "NOFORM")
        self.assertIsNone(response.context["link_form"])

    def test_anonymous_is_sent_to_login(self):
        response = self.client.post(self.link_url, {"plasmid": self.plasmid.pk})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)
        self.assertFalse(StrainPlasmid.objects.exists())

    def test_student_cannot_link_or_unlink(self):
        link = StrainPlasmid.objects.create(strain=self.strain, plasmid=self.plasmid)
        self.client.force_login(self.student)
        self.assertEqual(
            self.client.post(self.link_url, {"plasmid": self.plasmid.pk}).status_code, 403
        )
        self.assertEqual(self.client.post(self.unlink_url(link)).status_code, 403)
        self.assertTrue(StrainPlasmid.objects.filter(pk=link.pk).exists())

    def test_staff_links_a_plasmid_with_a_note_and_audit_fields(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            self.link_url, {"plasmid": self.plasmid.pk, "notes": "from box 3"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("strains:detail", args=[self.strain.pk]))
        link = StrainPlasmid.objects.get()
        self.assertEqual(
            (link.strain, link.plasmid, link.notes), (self.strain, self.plasmid, "from box 3")
        )
        self.assertEqual((link.created_by, link.updated_by), (self.staff, self.staff))
        page = self.client.get(response.url)
        self.assertContains(page, "LINK%d pEX-700 from box 3" % link.pk)
        self.assertContains(page, "MSG Plasmid pEX-700 was linked to Example-700.")

    def test_linking_the_same_plasmid_twice_shows_a_friendly_error(self):
        StrainPlasmid.objects.create(strain=self.strain, plasmid=self.plasmid)
        self.client.force_login(self.staff)
        response = self.client.post(self.link_url, {"plasmid": self.plasmid.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This strain already carries this plasmid.")
        self.assertEqual(StrainPlasmid.objects.count(), 1)

    def test_an_unknown_plasmid_is_a_form_error_not_a_crash(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.link_url, {"plasmid": 999999})
        self.assertEqual(response.status_code, 200)
        self.assertIn("plasmid", response.context["link_form"].errors)

    def test_the_link_urls_accept_post_only(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.link_url).status_code, 405)

    def test_unlinking_keeps_both_records(self):
        link = StrainPlasmid.objects.create(strain=self.strain, plasmid=self.plasmid)
        self.client.force_login(self.staff)
        response = self.client.post(self.unlink_url(link))
        self.assertEqual(response.url, reverse("strains:detail", args=[self.strain.pk]))
        self.assertFalse(StrainPlasmid.objects.exists())
        self.assertTrue(Strain.objects.filter(pk=self.strain.pk).exists())
        self.assertTrue(Plasmid.objects.filter(pk=self.plasmid.pk).exists())
        self.assertContains(
            self.client.get(response.url), "MSG Plasmid pEX-700 is no longer linked"
        )

    def test_unlink_with_the_wrong_strain_is_a_404_and_deletes_nothing(self):
        other = Strain.objects.create(strain_id="Example-701")
        link = StrainPlasmid.objects.create(strain=other, plasmid=self.plasmid)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(self.unlink_url(link)).status_code, 404)
        self.assertTrue(StrainPlasmid.objects.filter(pk=link.pk).exists())

    def test_get_on_unlink_is_not_allowed(self):
        link = StrainPlasmid.objects.create(strain=self.strain, plasmid=self.plasmid)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.unlink_url(link)).status_code, 405)
        self.assertTrue(StrainPlasmid.objects.filter(pk=link.pk).exists())
