"""Tests for "delete with a choice" on strains, plasmids and primers (core/delete.py)."""

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.core.delete import DeleteChoiceForm
from apps.core.tests.helpers import make_user, stub_templates
from apps.plasmids.models import Plasmid, PlasmidPrimerLink
from apps.primers.models import Primer
from apps.strains.models import Strain, StrainPlasmid

CONFIRM = (
    "DELETE {{ object }}"
    "{% for i in linked_exclusive %} EXCLUSIVE {{ i.kind }} {{ i.record }} {{ i.detail_url_name }}"
    "{% endfor %}"
    "{% for i in linked_shared %} SHARED {{ i.kind }} {{ i.record }}{% endfor %}"
    " BOX {{ form.delete_linked }}"
)
LIST = "{% for m in messages %}MSG {{ m }}{% endfor %}"
STUBS = {
    "primers/primer_confirm_delete.html": CONFIRM,
    "plasmids/plasmid_confirm_delete.html": CONFIRM,
    "strains/strain_confirm_delete.html": CONFIRM,
    "primers/primer_list.html": LIST,
    "plasmids/plasmid_list.html": LIST,
    "strains/strain_list.html": LIST,
}


class DeleteChoiceFormTest(TestCase):
    def test_the_box_is_off_by_default(self):
        form = DeleteChoiceForm({})
        self.assertTrue(form.is_valid())
        self.assertFalse(form.cleaned_data["delete_linked"])


@stub_templates(STUBS)
class DeleteWithChoiceTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)
        cls.admin = make_user("Admin")
        cls.staff = make_user("Staff")
        cls.student = make_user("Student")

    def url(self, kind, record):
        return reverse(f"{kind}:delete", args=[record.pk])

    def delete(self, kind, record, delete_linked=False):
        data = {"delete_linked": "on"} if delete_linked else {}
        return self.client.post(self.url(kind, record), data, follow=True)

    # --- permissions ---------------------------------------------------------------------
    def test_anonymous_is_sent_to_login(self):
        primer = Primer.objects.create(primer_id="P-1", sequence="ATGC")
        url = self.url("primers", primer)
        self.assertRedirects(self.client.get(url), f"{reverse('accounts:login')}?next={url}")

    def test_only_the_delete_permission_may_delete(self):
        primer = Primer.objects.create(primer_id="P-1", sequence="ATGC")
        plasmid = Plasmid.objects.create(plasmid_name="pEX-1")
        strain = Strain.objects.create(strain_id="S-1")
        for role in (self.student, self.staff):
            self.client.force_login(role)
            for kind, record in [("primers", primer), ("plasmids", plasmid), ("strains", strain)]:
                self.assertEqual(self.client.get(self.url(kind, record)).status_code, 403)
                self.assertEqual(self.client.post(self.url(kind, record)).status_code, 403)
        self.assertTrue(
            Primer.objects.exists() and Plasmid.objects.exists() and Strain.objects.exists()
        )

    # --- a record without links -----------------------------------------------------------
    def test_a_record_without_links_deletes_simply(self):
        self.client.force_login(self.admin)
        for kind, model, record in [
            ("primers", Primer, Primer.objects.create(primer_id="P-1", sequence="ATGC")),
            ("plasmids", Plasmid, Plasmid.objects.create(plasmid_name="pEX-1")),
            ("strains", Strain, Strain.objects.create(strain_id="S-1")),
        ]:
            page = self.client.get(self.url(kind, record))
            self.assertNotContains(page, "EXCLUSIVE")
            self.assertNotContains(page, "SHARED")
            response = self.delete(kind, record)
            self.assertContains(response, "MSG Deleted")
            self.assertFalse(model.objects.exists())

    # --- primers ---------------------------------------------------------------------------
    def make_primer_case(self):
        """P-1 binds pEX-solo (only P-1) and pEX-shared (also another primer and a strain)."""
        primer = Primer.objects.create(primer_id="P-1", sequence="ATGC")
        other = Primer.objects.create(primer_id="P-2", sequence="GGCC")
        solo = Plasmid.objects.create(plasmid_name="pEX-solo")
        shared = Plasmid.objects.create(plasmid_name="pEX-shared")
        PlasmidPrimerLink.objects.create(plasmid=solo, primer=primer)
        PlasmidPrimerLink.objects.create(plasmid=shared, primer=primer)
        PlasmidPrimerLink.objects.create(plasmid=shared, primer=other)
        return primer, solo, shared

    def test_primer_page_splits_exclusive_and_shared(self):
        primer, solo, shared = self.make_primer_case()
        self.client.force_login(self.admin)
        page = self.client.get(self.url("primers", primer))
        self.assertContains(page, "EXCLUSIVE plasmid pEX-solo plasmids:detail")
        self.assertContains(page, "SHARED plasmid pEX-shared")
        self.assertContains(page, "BOX")

    def test_primer_delete_only_this_record_keeps_the_plasmids(self):
        primer, solo, shared = self.make_primer_case()
        self.client.force_login(self.admin)
        response = self.delete("primers", primer)
        self.assertContains(response, "MSG Deleted primer P-1.")
        self.assertFalse(Primer.objects.filter(pk=primer.pk).exists())
        self.assertEqual(Plasmid.objects.count(), 2)
        self.assertEqual(PlasmidPrimerLink.objects.count(), 1)  # only P-2's link is left

    def test_primer_also_delete_removes_only_the_exclusive_plasmid(self):
        primer, solo, shared = self.make_primer_case()
        self.client.force_login(self.admin)
        response = self.delete("primers", primer, delete_linked=True)
        self.assertContains(
            response, "MSG Deleted primer P-1 and the linked records: plasmid pEX-solo."
        )
        self.assertEqual(
            list(Plasmid.objects.values_list("plasmid_name", flat=True)), ["pEX-shared"]
        )
        self.assertEqual(Primer.objects.get().primer_id, "P-2")

    # --- plasmids --------------------------------------------------------------------------
    def make_plasmid_case(self):
        """pEX-1 has primer P-solo (only here), P-shared (also on pEX-2), strain S-solo
        (carries only pEX-1), S-two (also carries pEX-2) and S-child (a child of S-solo)."""
        plasmid = Plasmid.objects.create(plasmid_name="pEX-1")
        other = Plasmid.objects.create(plasmid_name="pEX-2")
        p_solo = Primer.objects.create(primer_id="P-solo", sequence="ATGC")
        p_shared = Primer.objects.create(primer_id="P-shared", sequence="GGCC")
        PlasmidPrimerLink.objects.create(plasmid=plasmid, primer=p_solo)
        PlasmidPrimerLink.objects.create(plasmid=plasmid, primer=p_shared)
        PlasmidPrimerLink.objects.create(plasmid=other, primer=p_shared)
        s_solo = Strain.objects.create(strain_id="S-solo")
        s_two = Strain.objects.create(strain_id="S-two")
        StrainPlasmid.objects.create(strain=s_solo, plasmid=plasmid)
        StrainPlasmid.objects.create(strain=s_two, plasmid=plasmid)
        StrainPlasmid.objects.create(strain=s_two, plasmid=other)
        return plasmid, other

    def test_plasmid_page_splits_exclusive_and_shared(self):
        plasmid, other = self.make_plasmid_case()
        self.client.force_login(self.admin)
        page = self.client.get(self.url("plasmids", plasmid))
        self.assertContains(page, "EXCLUSIVE primer P-solo")
        self.assertContains(page, "EXCLUSIVE strain S-solo strains:detail")
        self.assertContains(page, "SHARED primer P-shared")
        self.assertContains(page, "SHARED strain S-two")

    def test_plasmid_delete_only_this_record_keeps_primers_and_strains(self):
        plasmid, other = self.make_plasmid_case()
        self.client.force_login(self.admin)
        self.delete("plasmids", plasmid)
        self.assertFalse(Plasmid.objects.filter(pk=plasmid.pk).exists())
        self.assertEqual(Primer.objects.count(), 2)
        self.assertEqual(Strain.objects.count(), 2)

    def test_plasmid_also_delete_removes_only_exclusive_primers_and_strains(self):
        plasmid, other = self.make_plasmid_case()
        self.client.force_login(self.admin)
        self.delete("plasmids", plasmid, delete_linked=True)
        self.assertEqual(sorted(Primer.objects.values_list("primer_id", flat=True)), ["P-shared"])
        self.assertEqual(sorted(Strain.objects.values_list("strain_id", flat=True)), ["S-two"])
        self.assertEqual(Plasmid.objects.get().plasmid_name, "pEX-2")
        # The other plasmid keeps its link to the shared primer and to the shared strain.
        self.assertEqual(PlasmidPrimerLink.objects.count(), 1)
        self.assertEqual(StrainPlasmid.objects.count(), 1)

    def test_a_strain_with_a_child_is_never_deleted_with_a_plasmid(self):
        plasmid = Plasmid.objects.create(plasmid_name="pEX-1")
        parent = Strain.objects.create(strain_id="S-parent")
        Strain.objects.create(strain_id="S-child", parent_strain=parent)
        StrainPlasmid.objects.create(strain=parent, plasmid=plasmid)
        self.client.force_login(self.admin)
        self.assertContains(
            self.client.get(self.url("plasmids", plasmid)), "SHARED strain S-parent"
        )
        self.delete("plasmids", plasmid, delete_linked=True)
        self.assertEqual(Strain.objects.count(), 2)

    # --- strains ---------------------------------------------------------------------------
    def make_strain_case(self):
        """S-1 carries pEX-solo (only S-1), pEX-two (also another strain) and pEX-primer
        (has a primer)."""
        strain = Strain.objects.create(strain_id="S-1")
        other = Strain.objects.create(strain_id="S-2")
        solo = Plasmid.objects.create(plasmid_name="pEX-solo")
        two = Plasmid.objects.create(plasmid_name="pEX-two")
        with_primer = Plasmid.objects.create(plasmid_name="pEX-primer")
        for plasmid in (solo, two, with_primer):
            StrainPlasmid.objects.create(strain=strain, plasmid=plasmid)
        StrainPlasmid.objects.create(strain=other, plasmid=two)
        PlasmidPrimerLink.objects.create(
            plasmid=with_primer, primer=Primer.objects.create(primer_id="P-1", sequence="ATGC")
        )
        return strain

    def test_strain_page_splits_exclusive_and_shared(self):
        strain = self.make_strain_case()
        self.client.force_login(self.admin)
        page = self.client.get(self.url("strains", strain))
        self.assertContains(page, "EXCLUSIVE plasmid pEX-solo")
        self.assertContains(page, "SHARED plasmid pEX-two")
        self.assertContains(page, "SHARED plasmid pEX-primer")

    def test_strain_delete_only_this_record_keeps_the_plasmids(self):
        strain = self.make_strain_case()
        self.client.force_login(self.admin)
        self.delete("strains", strain)
        self.assertFalse(Strain.objects.filter(pk=strain.pk).exists())
        self.assertEqual(Plasmid.objects.count(), 3)
        self.assertEqual(StrainPlasmid.objects.count(), 1)  # only S-2's link is left

    def test_strain_also_delete_removes_only_the_exclusive_plasmid(self):
        strain = self.make_strain_case()
        self.client.force_login(self.admin)
        self.delete("strains", strain, delete_linked=True)
        names = sorted(Plasmid.objects.values_list("plasmid_name", flat=True))
        self.assertEqual(names, ["pEX-primer", "pEX-two"])
        self.assertEqual(Primer.objects.count(), 1)
        self.assertEqual(Strain.objects.get().strain_id, "S-2")

    def test_deleting_a_strain_keeps_its_children(self):
        parent = Strain.objects.create(strain_id="S-parent")
        child = Strain.objects.create(strain_id="S-child", parent_strain=parent)
        self.client.force_login(self.admin)
        self.delete("strains", parent, delete_linked=True)
        child.refresh_from_db()
        self.assertIsNone(child.parent_strain)
