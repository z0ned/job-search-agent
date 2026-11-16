*REQUIREMENTS CONSOLIDATION  /  NOVEMBER 16, 2026*

# Job Search Agent — MVP Requirements

Version 1.1  |  Consolidated decisions and outstanding design questions

**Product objective**

Build a locally hosted, AI-powered system that discovers new job postings daily, deduplicates them, evaluates fit against a professional profile, ranks opportunities, emails top new recommendations, learns from approved feedback, and explores adjacent career paths.

STATUS  Requirements definition is substantially advanced; implementation has not started. Confirmed decisions are distinguished from proposed technology and open questions.

## 1. Executive summary

The MVP is a recommendation system, not an application-management platform. It runs on a home computer and exposes a local browser dashboard. It stores all jobs that pass eligibility filters, emails only the highest-ranked newly discovered jobs, and learns from detailed Interested and Rejected feedback only after explicit approval of the AI’s interpretation.

The new measurement framework makes recommendation quality testable. The first 50 ordinary recommendations form a frozen-learning baseline. Approved learning is then applied once; the next 50 recommendations are evaluated with learning frozen again. A gain of at least 10 percentage points in recommendation precision is the practical success target. Five lower-ranked jobs are also reviewed blindly each week to reveal missed opportunities.

### Decision classification used in this document

| Label | Meaning |
| --- | --- |
| CONFIRMED | Explicitly selected in the requirements sessions or stated in the original MVP brief. |
| PROPOSED | Recommended design choice or candidate technology; not yet approved. |
| OPEN | Requires a later decision. No default is silently assumed. |

### What has changed since the original summary

- Defined “Interested” as a job the user would seriously consider applying for.
- Selected mandatory free-form feedback for both Interested and Rejected decisions, interpreted by AI.
- Required approval of AI interpretations through a separate batch-review queue; ambiguous comments require clarification.
- Defined weekly blind missed-opportunity audits and a controlled 50 + 50 evaluation plan.
- Defined a +10-percentage-point improvement target and investigation/pause responses for underperformance.
## 2. Scope and operating boundaries

### 2.1 In scope — confirmed

| Area | Requirement |
| --- | --- |
| Local operation | Run on a home computer; browser-based dashboard, local access only. No cloud hosting requirement. |
| Daily discovery | Run automatic daily searches across multiple sources, including direct employer feeds/boards where accessible; no manual or custom search button in the MVP. |
| Recommendation workflow | Normalize, deduplicate, apply mandatory eligibility criteria, assess, rank, store, and notify. |
| Review and archives | Support Unreviewed, Interested, and Rejected / Archived; preserve rejected jobs with dates and explanations. |
| Personalization | Import resumes, perform an initial profile interview, accept manual profile edits, and learn only from approved interpretations. |
| Career discovery | Maintain a Career Opportunity Map and search for adjacent/unfamiliar role categories. |
| Quality monitoring | Measure recommendation precision and examine lower-ranked opportunities using a weekly blind audit. |

### 2.2 Explicitly out of scope — confirmed

- Application tracking, interview management, and application follow-up.
- Cloud-hosted dashboard or remote access for MVP.
- Manual on-demand job searches and user-configured custom searches in MVP.
### 2.3 User-visible workflow

1. The daily scheduled job gathers postings from available providers and employer feeds.
1. The agent normalizes, merges duplicate listings, and eliminates clear hard-criteria violations.
1. The agent scores and explains every qualifying job, keeps all of them in the dashboard, and emails a shortlist of only new top-ranked postings.
1. The user reviews jobs and submits a decision with a free-form explanation.
1. The AI proposes structured feedback interpretations in a separate learning queue. The user reviews, corrects, and bulk-approves them later.
1. Only approved interpretations are allowed to influence learning, subject to evaluation-phase freezes.
## 3. Functional requirements

### 3.1 Collection, scoring, and notification

| ID | MVP requirement |
| --- | --- |
| FR-01 | Automatically collect jobs every day from multiple accessible job sources and direct employer feeds or boards. |
| FR-02 | Normalize source fields to a common posting model and retain original source identifiers and links. |
| FR-03 | Recognize duplicate postings across sources and successive days; do not reintroduce the same opportunity as new. |
| FR-04 | Exclude postings that clearly violate configured mandatory eligibility rules; retain uncertainty where facts are missing. |
| FR-05 | Evaluate qualifications, transferable strengths, gaps, concerns, responsibilities, and interest alignment; provide a score and rationale. |
| FR-06 | Save all qualifying jobs and rank the Unreviewed list by relevance. |
| FR-07 | Email a brief daily shortlist of highest-ranked newly discovered postings with dashboard links; do not re-email previously discovered jobs as new. |
| FR-08 | Recover or visibly report missed/failed scheduled searches; exact retry behavior remains open. |

### 3.2 Dashboard, profile, and career exploration

| ID | MVP requirement |
| --- | --- |
| FR-09 | Provide separate dashboard views for Unreviewed, Interested, and Rejected / Archived jobs. |
| FR-10 | Display job facts, source link, match score, qualification comparison, strengths, gaps, concerns, and ranking explanation in normal job detail. |
| FR-11 | Store the Interested or Rejected decision, its submission date, and the original user explanation. |
| FR-12 | Import resumes, support an initial profile interview, and permit manual updates to background and preferences. |
| FR-13 | Distinguish confirmed profile facts and explicitly declared preferences from AI-derived inferences. |
| FR-14 | Maintain Career Opportunity Map fields: category, interest, career fit, confidence, market opportunity, and trend. |
| FR-15 | Discover potentially relevant adjacent career categories while continuing to enforce mandatory eligibility constraints. |

### 3.3 Free-form feedback and guarded learning

| ID | MVP requirement |
| --- | --- |
| FR-16 | Require at least one written free-form reason before saving an Interested decision; Interested means “I would seriously consider applying for this job.” |
| FR-17 | Capture rejection reasons as required free-form explanations rather than mandatory fixed-category selections. |
| FR-18 | Use AI to interpret comments into one or more positive, negative, and uncertain attribute-level preference signals; preserve the exact original text. |
| FR-19 | Keep role/responsibilities, employer/industry, compensation, work arrangement, seniority/scope, and other reasons distinct. A rejection for one attribute must not reject an entire career category. |
| FR-20 | Queue AI interpretations for later batch review; job review itself must not be interrupted for interpretation approval. |
| FR-21 | Allow correction of erroneous interpretations; then approve remaining reviewed interpretations together in a single bulk action. |
| FR-22 | Flag ambiguous feedback as Needs Clarification and request an explanation in the queue before proposing learning. |
| FR-23 | Never apply unapproved interpretations. Keep explicit mandatory criteria unchanged unless separately authorized. |

### 3.4 Audit, measurement, and quality control

| ID | MVP requirement |
| --- | --- |
| FR-24 | Each week, randomly select five eligible lower-ranked jobs for a separate Discovery Audit. |
| FR-25 | In audits, conceal all match scores, assessments, and recommendation rationales until Interested/Rejected decisions and written reasons exist for all five jobs. |
| FR-26 | After all five reviews, reveal their saved original AI assessments together; preserve original scores and ranks for analysis. |
| FR-27 | Compute baseline precision using the first 50 ordinarily recommended, fully reviewed jobs grouped into five sets of ten; exclude audit jobs. |
| FR-28 | Keep recommendation-learning parameters frozen through jobs 1–50; collect and approve feedback without applying learned updates. |
| FR-29 | Apply approved baseline learning once, then freeze learned ranking parameters through ordinary recommendations 51–100. |
| FR-30 | Compare performance across the two 50-job phases; a gain of ≥10 percentage points is the MVP meaningful-improvement target. |
| FR-31 | After the controlled comparison, use a rolling window of the most recent 50 reviewed recommendations to measure ongoing results. |
| FR-32 | If initial target is missed, investigate before continuous learning; after implementing corrective changes, resume continuous learning without requiring another 50-job controlled test. |
| FR-33 | If ongoing precision deteriorates past an agreed threshold, pause applying learning updates and investigate; daily collection and recommendation continue. Exact threshold is OPEN. |

## 4. Job decisions and feedback semantics

| Job status | Definition / action |
| --- | --- |
| Unreviewed | Qualifying posting not yet marked Interested or Rejected. |
| Interested | The user would seriously consider applying; written explanation is mandatory. |
| Rejected / Archived | The user does not wish to pursue this posting; preserve the original posting, explanation, and decision date. |

INTERPRETATION RULE  Interested is a positive signal about the job, but not automatic approval of every job attribute. Rejected is a negative decision on the posting, but not automatically on the career category.

## 5. Learning Approval Queue

### 5.1 Confirmed batch workflow

1. User records Interested/Rejected and provides a required free-form explanation; the job decision is saved immediately.
1. The AI retains the original text and produces proposed structured interpretations without modifying learned preferences.
1. Clear proposed interpretations are added to the Pending Approval queue; ambiguous explanations are marked Needs Clarification.
1. During a later batch session, the user clarifies unclear items and corrects any faulty interpretations.
1. The user approves the remaining interpretations together through one explicit bulk action.
1. Approved learning updates are applied only when the current evaluation phase permits learning.
### 5.2 Interpretation dimensions

| Dimension | Examples / boundary |
| --- | --- |
| Position / responsibilities | Nature of daily duties, problem-solving, client interaction, sales responsibilities, etc. |
| Employer / industry | Reaction to a specific company or sector; does not necessarily generalize to the role. |
| Compensation | Base pay, contract rate, benefits or compensation structure. |
| Working arrangement | Remote/hybrid/onsite, location, travel requirement, schedule. |
| Seniority / scope | Breadth of accountability and desired level of responsibility. |
| Other / nuance | Transferable skills, career growth, purpose, colleagues, and explanation-specific factors. |

### 5.3 Interpretation record — recommended data shape

| Field | Purpose |
| --- | --- |
| Original feedback | Immutable user-authored text and job decision. |
| Proposed signal(s) | Structured attributes, polarity, context, and AI confidence. |
| Review state | Needs Clarification / Pending Approval / Approved; optionally dismissed if user declines. |
| Clarification + correction | User-authored additional explanation and adjusted interpretation. |
| Approval metadata | Approval timestamp and model/profile version affected. |
| Application status | Pending application to preferences during freeze; applied when permitted. |

DESIGN DISTINCTION  Approval of an interpretation and application of an approved change are separate events. This is necessary during the first and second 50-job learning freezes.

## 6. Recommendation quality measurement

### 6.1 Primary metric: Precision@10

Precision@10 = number of Interested decisions among a fully reviewed top-ranked group of ten ÷ 10. The baseline and comparison each contain five completed groups of ten ordinary recommendations. Unreviewed postings do not count as Rejected; incomplete groups are reported as incomplete. Weekly audit jobs never enter the primary evaluation denominator.

### 6.2 Controlled evaluation phases — confirmed

| Phase | Population | Learning behavior | Evaluation / gate |
| --- | --- | --- | --- |
| 1. Baseline | Ordinary jobs 1–50 | Freeze learned preference/ranking updates; collect and approve interpretation proposals. | Preserve original model/profile versions; calculate baseline precision. |
| 2. Comparison | Ordinary jobs 51–100 | Apply approved baseline learning once, then freeze again. | Compare precision with baseline; success threshold: +10 percentage points. |
| 3. Continuous | Ordinary jobs 101 onward | Apply only approved learning updates (unless paused for quality investigation). | Monitor most recent 50 reviewed normal recommendations. |

### 6.3 Worked example (illustrative, not actual results)

| Measure | Phase 1 | Phase 2 | Difference |
| --- | --- | --- | --- |
| Interested / 50 | 20 / 50 | 25 / 50 | 5 more |
| Precision | 40% | 50% | +10 percentage points |
| Interpretation | Baseline | Improved candidate | Meets practical MVP target; not statistical proof |

### 6.4 Supporting measures

| Measure | Definition and intended use |
| --- | --- |
| Hard-criteria violations | Number of recommendations contrary to known mandatory rules; target proposed: zero. |
| Missed-opportunity rate | Interested decisions ÷ completed reviews among the five weekly randomly sampled lower-ranked jobs. |
| Preference interpretation accuracy | Corrected vs accepted AI signals, including ambiguity frequency; guard against bad learning. |
| Career exploration value | Interest in unfamiliar categories, tracked separately from familiar-category precision. |
| Job supply and freshness | Qualifying jobs discovered, source failures, duplicate suppression, and old postings resurfacing. |

STATISTICAL CAUTION  A two-period 50-versus-50 change is a practical product target, not causal proof. Preserve original rankings and model versions; common labeled jobs can provide additional diagnostics.

## 7. Weekly Discovery Audit

### 7.1 Confirmed audit rules

| Rule | Behavior |
| --- | --- |
| Cadence / sample | Weekly; five randomly selected jobs from eligible postings below the normal top-ranked recommendations. |
| Blind condition | Hide all AI scores, rankings, comparisons, and explanations throughout the entire five-job audit. |
| Required feedback | Interested or Rejected, with required free-form explanation for each job. |
| Reveal condition | Only after all five have been reviewed, show their saved original AI assessments together. |
| Learning | Proposed interpretations enter the ordinary batch approval queue; no unapproved learning. |
| Measurement | Audit interest rate measures attractive jobs present in the sampled lower-ranked pool; review over multiple weeks. |

### 7.2 Guardrails for valid measurement — recommended

- Select eligible and not-yet-reviewed jobs without looking at whether the AI expects them to be attractive.
- Preserve selection date, sampled pool, random seed or selection identifier, and original model version for repeatability.
- Carry incomplete audits forward without revealing scores; do not treat absent decisions as negative feedback.
- Sample from a clearly defined lower-ranked population; decide later how to handle very small weekly candidate pools.
## 8. Professional profile and Career Opportunity Map

### 8.1 Profile

Confirmed profile inputs: resume import, initial interview, manual edits, and approved feedback. Explicit skills, experience, and preferences must be separated from AI inferences. Hard criteria are never silently rewritten by learning.

### 8.2 Opportunity Map

| Field | Meaning |
| --- | --- |
| Career category | Known or newly discovered role family. |
| Interest score | Learned degree of attraction, based on approved feedback. |
| Career fit score | Suitability given experience, qualifications, and transferable skills. |
| Confidence score | Strength of evidence behind inferred category assessments. |
| Market opportunity score | Volume or quality of currently discovered eligible postings. |
| Trend indicator | Whether learned interest or the opportunity picture is increasing or decreasing. |

PROPOSED; NOT FINALIZED  Approximately 80% recommendations from known interests and 20% from exploratory categories. The exploration proportion and diversity policy remain OPEN; every exploratory job must still respect hard eligibility constraints.

## 9. MVP solution outline (proposed, not approved)

The original requirements proposed the following straightforward local stack. This document does not finalize vendor choice or prescribe the detailed architecture.

| Component | Candidate | Responsibility |
| --- | --- | --- |
| Local dashboard | Streamlit | Review jobs, profile, Career Opportunity Map, learning queue, audits, and quality scorecard. |
| Application / services | Python 3.12+ | Source adapters, normalization, deduplication, eligibility, ranking, feedback, metrics. |
| Local storage | SQLite | Persist postings, job decisions, feedback, interpretation workflow, profile, and metrics. |
| Scheduling | OS scheduler / Python | Daily runs, missed-run recovery, health and error recording. |
| AI evaluation | OpenAI API | Structured job assessments and interpretation proposals. |
| Posting sources | Adzuna + employer APIs/feeds | Collect postings; final providers to be selected after feasibility checks. |
| Email sending | Gmail API | Send brief daily digest of the best newly discovered jobs. |

### 9.1 Logical data entities (initial design proposal)

| Entity | Key information / relationships |
| --- | --- |
| JobPosting | Canonical job ID, posting content, employer, role, source URLs, first/last seen, availability. |
| SourceObservation | Source provider, external listing ID, observed timestamp, original URL; many observations can map to one job. |
| JobAssessment | Job, scoring-model version, profile version, fit dimensions, rationale, ranking, evaluated timestamp. |
| JobDecision | Job, user decision, decision date, original required feedback text. |
| FeedbackInterpretation | Decision, structured signals, clarification/correction content, approval state and timestamps. |
| Preference / ProfileVersion | Confirmed rules, versioned skills/preferences, approved learned weights; keep audit trail. |
| CareerCategory | Category identity and map scores, confidence, market opportunity, trend. |
| AuditBatch / AuditItem | Weekly blind sample, stored original assessment, review completion, reveal timestamp. |
| EvaluationWindow | Baseline/comparison/rolling period, eligible decisions, metric values, model version. |

### 9.2 Important local-hosting consideration

The dashboard runs locally, but posting providers, the OpenAI API, and Gmail require internet access. Email links pointing to localhost will generally open the dashboard only on the computer running the app. Remote mobile access is not part of the MVP.

## 10. Non-functional requirements and acceptance criteria

### 10.1 Non-functional expectations

| Area | MVP expectation / status |
| --- | --- |
| Reliability | Daily operation and restart recovery should be observable; exact schedule/retry design OPEN. |
| Integrity | Repeated source observations must not create duplicate canonical jobs or duplicate “new” emails. |
| Explainability | Retain original job text, feedback, proposed signals, corrections, approvals, and ranking rationale. |
| Privacy / security | Store secrets outside source code, restrict dashboard to local access, and protect local resume and feedback data. |
| Maintainability | Small, modular Python services with versioned rules and source adapters; avoid overengineering. |
| Cost | No cloud hosting expense; external API usage and job-data providers may incur costs. |
| Availability | Agent should reveal failures or partial collection results rather than presenting an incomplete run as fully successful. |

### 10.2 Initial acceptance tests

| ID | Acceptance condition |
| --- | --- |
| AT-01 | Two sightings of the same job through separate feeds result in one canonical dashboard listing and no repeat “new” email. |
| AT-02 | A known mandatory constraint violation is excluded from recommendation and email ranking. |
| AT-03 | Interested and Rejected cannot be submitted without free-form reasons; original text is retrievable. |
| AT-04 | A salary-only rejection produces no automatic negative update to the career-category interest score. |
| AT-05 | Ambiguous comments appear under Needs Clarification, with no learned preference changes. |
| AT-06 | Pending interpretations never affect ranking; a corrected, explicitly bulk-approved batch is retained for audit. |
| AT-07 | No learned weights change during the first 50 reviews; exactly one approved update occurs before reviews 51–100, followed by a second freeze. |
| AT-08 | Five audit jobs remain blind until all decisions and explanations exist; original scores appear together afterward. |
| AT-09 | Precision counts only fully reviewed ordinary groups of ten, and excludes audit samples. |
| AT-10 | When a quality pause is in effect, daily collection and job notifications continue while preference-update application stops. |

## 11. Implementation plan and release gates

| Stage | Outcome / recommended deliverables |
| --- | --- |
| 1. Requirement completion | Decide eligibility filters, provider priorities, email size/time, lifecycle handling, and key metric thresholds. |
| 2. Discovery foundation | Implement source adapters, canonical posting store, deduplication, hard filters, and daily job-run logging. |
| 3. Recommendation MVP | Import profile, perform AI assessments/ranking, implement dashboard and brief daily digest. |
| 4. Guarded feedback | Implement mandatory explanations, AI structured interpretations, clarification queue, corrections, and bulk approval. |
| 5. Measurement | Implement versioned scoring, first 50-job freeze, second 50-job freeze, scorecards, weekly blind audit. |
| 6. Controlled validation | Compare Phase 1 and Phase 2. If gain is <10 points, investigate before continuous learning. |
| 7. Continuous mode | Enable approved preference updates and rolling 50-job monitoring; pause learning on validated quality deterioration. |

## 12. Risks and tradeoffs

| Risk / tradeoff | Mitigation or decision |
| --- | --- |
| Incomplete coverage / provider changes | Start with a few accessible reliable sources; expose partial runs and source errors. |
| Duplicate posts with varying identifiers | Use source IDs plus semantic employer/title/location matching, with conservative merge rules. |
| AI misinterpretation | Save original text, require explicit bulk approval, use Needs Clarification for ambiguous cases. |
| Feedback overgeneralization | Score attributes separately; avoid applying employer, pay, or travel rejection as category-wide dislike. |
| Cold start / evaluation delay | Use initial resume/interview for baseline; accept the two 50-job freezes to obtain comparisons. |
| Small samples / changing job market | Interpret +10 points as product target; use audits and retained reference jobs, not statistical proof. |
| Blind audit friction | Keep five-item weekly sample, persist incomplete progress, reveal only when complete. |
| Local-only convenience / uptime | OS-scheduled recovery and visible run health; dashboard email links usable mainly on host machine. |
| Approval backlog | Display pending count and support a single reviewed bulk approval action. |

## 13. Outstanding decisions — do not assume defaults

The following matters are still open. The specific review choices above are confirmed; these items remain unresolved even where an earlier discussion suggested a default.

| Category | Open question |
| --- | --- |
| Eligibility | Exact career categories, salary floor, location/remote boundaries, employment type, travel tolerance, and hard disqualifiers. |
| Daily operations | Execution time and what to do after the home PC was off; exact recovery/retry policy. |
| Email | Number of top new recommendations per message and whether local-dashboard-only links are sufficient. |
| Sources | Which job APIs, direct employer boards, and feeds to enable first; cost/access constraints. |
| Posting lifecycle | How to handle expired, inactive, refreshed, or reposted jobs; when a repost counts as new. |
| Ranking | Weights, minimum fit threshold, unknown compensation/requirements, and category diversity. |
| Career exploration | Whether to adopt the proposed 80% familiar / 20% exploratory split and how exploration is chosen. |
| Profile governance | Process for confirming inferred skills and manually proposed changes to hard rules. |
| Quality decline | Exact rolling-50 precision drop that triggers pause and investigation; benchmark selection. |
| Audit mechanics | Definition of “lower-ranked pool,” insufficient eligible jobs, and missed/unfinished audit timing. |
| Error reporting | Which dashboard health indicators and failure notifications are essential for MVP. |
| Batch approval UX | Treatment of declined AI interpretations and completion rules for corrections; detailed UI pattern. |

## 14. Requirements provenance and change log

### Source basis

Baseline document: “Job Search Agent — MVP requirements summary,” dated November 16, 2026 (four pages), supplied by the user. Consolidation also includes the subsequent interactive requirements decisions in this project conversation through the decision to pause learning and investigate declines. No outside research or new provider claims have been incorporated.

### Key changes in v1.1

Added explicit Interested semantics; required unstructured positive and negative feedback; AI-interpretation review with clarification and bulk approval; separate approval and activation of learned updates; weekly five-job blind audits; two frozen 50-job performance phases; +10 percentage-point improvement target; controlled failure investigation and continuous-monitoring pause behavior.

### Status summary

CONFIRMED  Product scope, local hosting, daily discovery, dashboard states, feedback collection and approval, audit mechanics, evaluation stages, and improvement target.

PROPOSED  Specific software stack, source suppliers, 80/20 exploration allocation, logical schema details, and secondary metric targets.

OPEN  Eligibility profile, operating schedule, email size, provider prioritization, posting lifecycle, ranking details, and performance-decline threshold.