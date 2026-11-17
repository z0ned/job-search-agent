# Sprint 1 — Greenhouse Recent Role × Contract Signal Overlap (2026-11-17)

**Result:** Public feed access passed on all five selected employer boards. Five-board contract opportunity feasibility for a U.S.-based applicant remains unproven.

**Execution:** User ran `scripts/feasibility/test_greenhouse_contract_overlap.ps1` locally on 2026-11-17 at 17:09:27 UTC. This test made one unauthenticated GET per Greenhouse employer board; no Adzuna calls.

## Actual observed counts

| Board | Non-prospect jobs | First published <=30 days ago | Broad role title signals | Contract title/metadata signals | Recent AND role AND contract signals |
|---|---:|---:|---:|---:|---:|
| gitlab | 253 | 115 | 23 | 2 | 0 |
| vercel | 87 | 18 | 11 | 1 | 0 |
| openmined | 15 | 15 | 3 | 0 | 0 |
| infuse | 269 | 165 | 126 | 250 | 63 |
| crunchyroll | 98 | 34 | 12 | 1 | 0 |
| **Total** | **722** | **347** | **175** | **254** | **63** |

All five feeds returned success, and all 722 reported non-prospect job listings had first-published dates. Across boards: recent+role = 83; recent+contract = 166; role+contract = 127; triple intersection = 63.

### Why 63 is not a U.S. contract supply count

All 63 triple-overlap records came from INFUSE, all with **both** contract-like title and metadata evidence (0 title-only, 0 metadata-only). Its employment metadata across 269 listings was:

| INFUSE `Type of contract` | Listings |
|---|---:|
| Non-US Contractor | 247 |
| UA Contractor | 3 |
| US Employee | 17 |
| INTL Employee | 1 |
| APAC Employee | 1 |

The script's contract-metadata signals are the 247 Non-US Contractor + 3 UA Contractor categories. Thus the 63 triple-overlap listings carry international/UA contractor type metadata rather than a `US Employee` type; they cannot be assumed eligible for a Georgia-based worker.

Among these 63, the title-location text contained literal Atlanta/Georgia terms on 2 records, but none contained the explicit literal tokens US, USA, United States or remote. Two Atlanta labels do **not** override conflicting employment metadata or establish hiring eligibility. The remote/US/Atlanta counts are literal label matches, not verified location or authorization filters.

**Conclusion:** Greenhouse passes five-board programmatic access, but **zero U.S.-eligible recent PM-contract openings have been verified** in this sample. This is not evidence that Greenhouse as a whole has zero such opportunities; only five employer boards were tested.

### Date/count reconciliation

The preceding run at 16:59:01 UTC found 721 jobs and 346 recently first-published. The run at 17:09:27 UTC found 722 and 347; GitLab increased from 252/114 to 253/115. This small change is not proof of sustained daily new-job volume.

## Recommendation

Proceed to **Lever public employer postings API** to test five employer boards for programmatic access, stable IDs, dated new postings where available, contract signals, geography and duplicate potential. Preserve the remaining Adzuna trial calls. No individual job suitability analysis and no production implementation yet.
