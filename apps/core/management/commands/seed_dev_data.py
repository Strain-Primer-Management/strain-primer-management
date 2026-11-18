from decimal import Decimal
from io import StringIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.plasmids.models import Plasmid, PlasmidPrimerLink
from apps.primers.models import Primer
from apps.strains.models import Strain, StrainPlasmid

# Every fake row carries this key in its extra_data, so --reset can find exactly these rows.
MARKER = {"seed_dev_data": True}
# Fake users carry this text in signup_note, so --reset never deletes a real user by accident.
MARKER_NOTE = "seed_dev_data: fake development user"

# Fake users, one per role: (username, role = group name, password). DEVELOPMENT ONLY.
USERS = [
    ("dev-student", "Student", "student-dev-pass"),
    ("dev-staff", "Staff", "staff-dev-pass"),
    ("dev-admin", "Admin", "admin-dev-pass"),
]

# (plasmid_name, size_bp, resistance, copy_number, promoter)
PLASMIDS = [
    ("pEX-01", 2686, "Ampicillin", "high", "lac"),
    ("pEX-02", 3450, "Kanamycin", "medium", "T7"),
    ("pEX-03", 4200, "Chloramphenicol", "low", "constitutive"),
    ("pEX-04", 5100, "Ampicillin", "high", "T7"),
    ("pEX-05", 6020, "Spectinomycin", "medium", "lac"),
    ("pEX-06", 7300, "Kanamycin", "low", "constitutive"),
    ("pEX-07", 3890, "Ampicillin, Kanamycin", "medium", "tac"),
    ("pEX-08", 4750, "Tetracycline", "low", "araBAD"),
    ("pEX-09", 8120, "Hygromycin", "medium", "GAL1"),
    ("pEX-10", 2950, "Ampicillin", "high", "T7"),
    ("pEX-11", 5600, "Gentamicin", "low", "rhaBAD"),
    ("pEX-12", 6400, "", "", ""),
]

# (primer_id, sequence, purpose): invented sequences.
PRIMERS = [
    ("P-001", "ATGCTAGCTTGACCGTAC", "Sequencing"),
    ("P-002", "GGTACGGTCAAGCTAGCAT", "Sequencing"),
    ("P-003", "TTGACGGCTAGCTCAGTCC", "PCR"),
    ("P-004", "CCTGAGCTAGCCGTCAAGG", "PCR"),
    ("P-005", "ACGTTGCAAGCTTGGATCC", "Cloning"),
    ("P-006", "GGATCCAAGCTTGCAACGT", "Cloning"),
    ("P-007", "CAGTCAGTCGATCGATCGA", "PCR"),
    ("P-008", "TCGATCGATCGACTGACTG", "PCR"),
    ("P-009", "GCTAGCTAGGATCCTAGGC", "Sequencing"),
    ("P-010", "GCCTAGGATCCTAGCTAGC", "Sequencing"),
    ("P-011", "AAGCTTGGCACTGGCCGTC", "Colony PCR"),
    ("P-012", "GACGGCCAGTGCCAAGCTT", "Colony PCR"),
    ("P-013", "TAATACGACTCACTATAGGG", "Sequencing"),
    ("P-014", "GCTAGTTATTGCTCAGCGG", "Sequencing"),
    ("P-015", "CGCGGATCCATGAAAGCTATT", "Cloning"),
    ("P-016", "CCGCTCGAGTTAGCCGTTAAC", "Cloning"),
    ("P-017", "GTAAAACGACGGCCAGT", "Sequencing"),
    ("P-018", "CAGGAAACAGCTATGAC", "Sequencing"),
    ("P-019", "TGACCATGATTACGCCAAGC", "Mutagenesis"),
    ("P-020", "GCTTGGCGTAATCATGGTCA", "Mutagenesis"),
    ("P-021", "ACCGTAGCTTAGGCT", "qPCR"),
    ("P-022", "AGCCTAAGCTACGGT", "qPCR"),
]

# (strain_id, host_organism, genotype, temp, medium, parent index or None, [plasmid indexes])
STRAINS = [
    ("Example-001", "E. coli K-12", "recA1, endA1, gyrA96", "37.0", "LB", None, [0]),
    ("Example-002", "E. coli K-12", "recA1, endA1, hsdR17", "37.0", "LB", 0, [0, 1]),
    ("Example-003", "E. coli BL21", "ompT, hsdSB", "30.0", "LB", None, [1]),
    ("Example-004", "E. coli BL21", "ompT, lon, hsdSB", "30.0", "M9", 2, [1, 3]),
    ("Example-005", "B. subtilis 168", "trpC2", "37.0", "LB", None, [2]),
    ("Example-006", "B. subtilis 168", "trpC2, amyE", "37.0", "M9", 4, [2, 4]),
    ("Example-007", "S. cerevisiae S288C", "MATalpha", "30.0", "YPD", None, []),
    ("Example-008", "E. coli K-12", "recA1", "37.0", "LB", 1, [5]),
    ("Example-009", "E. coli DH5alpha", "deoR, recA1, endA1", "37.0", "LB", None, [6, 9]),
    ("Example-010", "E. coli DH10B", "mcrA, araD139", "37.0", "SOB", None, [7]),
    ("Example-011", "E. coli Top10", "mcrA, lacZdeltaM15", "37.0", "LB", 9, [6]),
    ("Example-012", "P. putida KT2440", "wild type", "30.0", "LB", None, [10]),
    ("Example-013", "P. putida KT2440", "deltapvdD", "30.0", "M9", 11, [10, 2]),
    ("Example-014", "S. cerevisiae BY4741", "his3, leu2, met15, ura3", "30.0", "SC-Ura", None, [8]),
    ("Example-015", "S. cerevisiae BY4741", "his3, leu2, ura3, gal1", "30.0", "YPD", 13, [8]),
    ("Example-016", "C. glutamicum ATCC 13032", "wild type", "30.0", "BHI", None, []),
    ("Example-017", "E. coli MG1655", "ilvG, rph-1", "37.0", "M9", None, [9]),
    ("Example-018", "E. coli MG1655", "ilvG, rph-1, deltalacZ", "37.0", "M9", 16, [9, 0]),
    ("Example-019", "B. subtilis 168", "trpC2, deltasigF", "37.0", "LB", 5, [4]),
    ("Example-020", "Vibrio natriegens", "wild type", "37.0", "LB3", None, [3]),
    ("Example-021", "E. coli BL21", "ompT, lon, lacI", "25.0", "TB", 3, [1, 6]),
    ("Example-022", "S. cerevisiae S288C", "MATa, deltaade2", "30.0", "YPD", 6, []),
]

# (plasmid index, primer index, orientation, binding_position). Some primers are not linked.
LINKS = [
    (0, 0, "forward", "100-118"),
    (0, 1, "reverse", "900-918"),
    (1, 2, "forward", "250-268"),
    (1, 3, "reverse", "1240-1258"),
    (2, 4, "forward", "300-318"),
    (2, 5, "reverse", "1500-1518"),
    (3, 6, "forward", "420-438"),
    (4, 7, "reverse", "880-898"),
    (5, 8, "forward", "60-78"),
    (5, 9, "reverse", "2100-2118"),
    (6, 10, "forward", "510-528"),
    (6, 11, "reverse", "1330-1348"),
    (7, 12, "forward", "20-39"),
    (7, 13, "reverse", "1880-1898"),
    (8, 14, "forward", "700-720"),
    (8, 15, "reverse", "2400-2420"),
    (9, 16, "forward", "150-166"),
    (9, 17, "reverse", "420-436"),
    (9, 12, "forward", "40-59"),
    (10, 18, "forward", "930-949"),
    (10, 19, "reverse", "960-979"),
    (1, 12, "forward", "15-34"),
    (0, 16, "forward", "2500-2516"),
    (4, 14, "forward", "3100-3120"),
]


class Command(BaseCommand):
    """
    Fill the LOCAL database with obviously fake strains, plasmids, primers and users.

    Why: an empty app is hard to design pages for. Safe to run twice: a row that already
    exists is left alone. Every fake row is marked in extra_data (MARKER), so --reset
    removes only the rows this command made and never real data. Refuses to run when
    DEBUG is off, so it cannot fill a production database.
    """

    help = (
        "Create fake development data (strains, plasmids, primers, one user per role). "
        "DEVELOPMENT ONLY. Fake logins: dev-student / student-dev-pass, "
        "dev-staff / staff-dev-pass, dev-admin / admin-dev-pass. "
        "Use --reset to remove only the rows this command created."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Remove the fake rows this command created (nothing else), then stop.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_dev_data only runs when DEBUG is on (development only).")
        if options["reset"]:
            self.reset()
        else:
            self.seed()

    def reset(self):
        """Delete the fake rows. The link rows go with their strain or plasmid."""
        Strain.objects.filter(extra_data__seed_dev_data=True).delete()
        Plasmid.objects.filter(extra_data__seed_dev_data=True).delete()
        Primer.objects.filter(extra_data__seed_dev_data=True).delete()
        # Users have no extra_data: the fake ones are found by their fixed usernames, and only
        # if they are still marked by the signup note this command wrote.
        get_user_model().objects.filter(
            username__in=[u[0] for u in USERS], signup_note=MARKER_NOTE
        ).delete()
        self.stdout.write("Fake development data removed.")

    def seed(self):
        """Create whatever is missing; existing rows are not changed."""
        call_command("setup_roles", stdout=StringIO())  # the role groups must exist first
        staff_user = self.make_users()

        plasmids = [
            self.get_or_create(
                Plasmid,
                "plasmid_name",
                name,
                staff_user,
                size_bp=size,
                resistance_markers=resistance,
                sequence_file=f"{name}.dna",
                hessenbox_path=f"Example/{name}.dna",
                copy_number=copy,
                promoter_type=promoter,
                description="Fake plasmid for development.",
            )
            for name, size, resistance, copy, promoter in PLASMIDS
        ]
        primers = [
            self.get_or_create(
                Primer,
                "primer_id",
                primer_id,
                staff_user,
                sequence=sequence,
                purpose=purpose,
                freezer_location=f"Oligo Box {i // 6 + 1}, Pos {'ABCDEF'[i % 6]}{i % 12 + 1}",
            )
            for i, (primer_id, sequence, purpose) in enumerate(PRIMERS)
        ]
        strains = []
        for i, (strain_id, host, genotype, temp, medium, parent, _) in enumerate(STRAINS):
            strains.append(
                self.get_or_create(
                    Strain,
                    "strain_id",
                    strain_id,
                    staff_user,
                    host_organism=host,
                    genotype=genotype,
                    culturing_temp=Decimal(temp),
                    culturing_medium=medium,
                    freezer_location=f"Freezer {i % 4 + 1}, Box {i % 9 + 1}",
                    biosafety_level="BSL-2" if i % 7 == 6 else "BSL-1",
                    parent_strain=strains[parent] if parent is not None else None,
                )
            )

        # Links only between fake rows (a skipped real look-alike is None and is not linked).
        for strain, (*_, plasmid_indexes) in zip(strains, STRAINS, strict=True):
            for p in plasmid_indexes:
                if strain and plasmids[p]:
                    StrainPlasmid.objects.get_or_create(
                        strain=strain,
                        plasmid=plasmids[p],
                        defaults={"extra_data": MARKER, "created_by": staff_user},
                    )
        for p, r, orientation, position in LINKS:
            if plasmids[p] and primers[r]:
                PlasmidPrimerLink.objects.get_or_create(
                    plasmid=plasmids[p],
                    primer=primers[r],
                    orientation=orientation,
                    binding_position=position,
                    defaults={"extra_data": MARKER, "created_by": staff_user},
                )
        self.stdout.write(
            f"Fake data ready: {len(strains)} strains, {len(plasmids)} plasmids, "
            f"{len(primers)} primers, {len(USERS)} users."
        )

    def make_users(self):
        """Create the fake users (if missing) and return the staff one."""
        User = get_user_model()
        staff_user = None
        for username, role, password in USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.org",
                    "is_staff": role == "Admin",
                    "signup_note": MARKER_NOTE,
                },
            )
            if created:
                user.set_password(password)
                user.save()
                user.groups.add(Group.objects.get(name=role))
            if role == "Staff":
                staff_user = user
        return staff_user

    def get_or_create(self, model, key_field, key, created_by, **fields):
        """
        Return the fake row for this key, creating it if missing.

        A row with the same key that is NOT ours (a real one) is left alone: a warning is
        printed and None is returned, so nothing is linked to it.
        """
        existing = model.objects.filter(**{f"{key_field}__iexact": key}).first()
        if existing is None:
            return model.objects.create(
                **{key_field: key},
                **fields,
                extra_data=MARKER,
                created_by=created_by,
            )
        if existing.extra_data.get("seed_dev_data"):
            return existing
        self.stdout.write(f"Skipped {key}: a real row with this name exists.")
        return None
