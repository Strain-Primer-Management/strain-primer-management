# Domain & client requirements

Sources: the client's project description, their answers to our questions (Group_Questions),
and the team's data-model diagram. **Do not invent fields that are not listed here.** All
fields below are approved by the client (including the ones we first suggested). A Jira ticket
decides when each one is built.

## What the client wants

A web-based tool that replaces several Word files (Strains, Plasmids, Oligos in the Hessenbox
cloud) and becomes the lab's **single source of truth**:

- One central database with a clean, structured data model.
- A standardized, intuitive **input form** with **format-controlled input**.
- Fast **search and filtering**. Most common searches: strain **name**, **genetic properties**
  (genotype), **culturing requirements**.
- **Linked records**: open a strain → click its plasmid → open the plasmid in SnapGene → go on to
  its primers.
- **Individual logins** with roles; **backups**; a **script to import** the existing records
  (a bonus feature, to be discussed later).

Constraints from the client: **English-only UI**; **Windows desktop PCs** (rarely laptops/tablets);
SnapGene is installed on each PC; speed and accessibility matter most. The project listing also
says "Deutsch + Englisch" — the client's later answer (English only UI) wins; German is only
for talking to them. Decisions on hosting, files, licence: `docs/DECISIONS.md`.

## Entities

### Strain
`strain_id` (text, e.g. `Example-042`) · `host_organism` (e.g. E. coli K-12) · `genotype` (e.g.
recA1, endA1, gyrA96) · `culturing_temp` (decimal °C, e.g. 37.0) · `culturing_medium` (e.g. LB,
M9) · `freezer_location` (e.g. Freezer 2, Box 7) · `biosafety_level` · `parent_strain` (lineage,
optional) · `created_date` · `created_by`

### Plasmid
`plasmid_name` (e.g. pEX-12) · `size_bp` (integer) · `resistance_markers` (e.g. Ampicillin) ·
`sequence_file` (e.g. `pEX-12.dna`) · `hessenbox_path` (path inside the Hessenbox folder) ·
`copy_number` (High/Medium/Low) · `promoter_type` (e.g. T7, lac, constitutive) · `description`

### Primer (a.k.a. oligo)
`primer_id` (e.g. `P-017`) · `sequence` (5'→3', e.g. ATGCTAGCTTGACCGTAC) · `purpose`
(Sequencing, PCR, Cloning, …) · `melting_temp_tm` (calculated from the sequence) · `length_bp`
(counted from the sequence) · `freezer_location` (e.g. Oligo Box 1, Pos E4)

### Plasmid ↔ Primer link
A link table between the two, with `orientation` (Forward/Reverse) and `binding_position` (e.g. bp
1240-1260). These belong on the link, not on Plasmid or Primer.

### User
`username` · `email` · `role` = **Admin** (edit and delete, manage accounts) | **Staff** (view,
add, edit) | **Student** (view only). Implemented as Django groups + permissions (D7).

## Relationships

```
Strain  ──carries (M:N, optional)──▶  Plasmid  ──bound by (M:N via link table, optional)──▶  Primer
```

Every cardinality in the diagram is `0..*`: **all links are optional.** Therefore:

- A strain, plasmid or primer can be **created on its own**, with no relation, and linked later
  (or never).
- Strain lineage (`parent_strain`) is a nullable self-reference.
- **Deleting a record that has relations:** the user sees what is linked and **chooses** — delete
  only this record (default, its links disappear) or also delete the linked records. Nothing is
  ever deleted silently by the database (D8).

## Flexible columns

The client wants the columns to stay flexible. The fields above are real columns (typed,
searchable, validated); anything extra goes into one `extra_data` JSON field per entity (D6).

## Glossary

**Strain** a specific bacterial line with a defined genetic makeup (like a versioned build of an
organism) · **Plasmid** a small ring of DNA a bacterium carries (like a plug-in) · **Primer** a
short custom DNA snippet (~20 letters) marking where DNA is copied or read (like a search
pattern) · **SnapGene** desktop software to view/edit DNA sequences and plasmid maps ·
**Hessenbox** the university's Nextcloud cloud storage where the plasmid files live.
