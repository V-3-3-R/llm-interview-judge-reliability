# Protocol v0.1: Reliability of LLM-Based Technical Interview Evaluation

*Working title: Reliability of LLM-Based Technical Interview Evaluation: Agreement, Consistency, and Style Bias in Rubric-Based Grading*

Status: draft for the pilot. Thresholds below are provisional and should be frozen before any judge is run.

## 1. Research question

How reliably do LLM judges score technical interview answers against a fixed rubric, and how do answer style, verbosity, phrasing, rubric wording, and repeated runs change those scores when technical content is held constant?

**Scope:** DBMS answers only, pointwise scoring on a 0-5 scale, practice (formative) setting. Not hiring decisions.

## 2. Hypotheses (provisional thresholds)

| ID | Dimension | Hypothesis |
|---|---|---|
| H1 | Agreement | Under Rubric A, each judge reaches quadratic weighted kappa (QWK) ≥ 0.60 with the human consensus, and is within 0.10 of human-human QWK |
| H2 | Consistency | At default temperature, ≥ 10% of answers show a score range ≥ 1 point across 3 runs, a higher share than at temperature 0 |
| H3 | Style bias | At equal quality, the polished-jargon variant scores higher, and the poor-grammar variant lower, than the concise baseline by ≥ 0.3 points |
| H4 | Verbosity | At equal quality, the verbose variant scores higher than the concise baseline (paired, directional) |
| H5 | Rubric sensitivity | Switching Rubric A to Rubric B changes scores by a mean absolute difference ≥ 0.3 and shifts QWK versus humans |
| H6 | Sanity check | Incorrect answers score below correct answers in every style; the key risk cell is incorrect + polished |

Also test whether the **human** raters show the same style effects (Chen et al. found humans prefer longer answers too).

## 3. Design

**Variants per question:** 3 quality levels × 4 styles = 12.

| | S1 Concise (baseline) | S2 Verbose | S3 Poor grammar / non-native phrasing | S4 Polished, jargon-heavy |
|---|---|---|---|---|
| **Correct** | C-S1 | C-S2 | C-S3 | C-S4 |
| **Partial** (one key concept missing) | P-S1 | P-S2 | P-S3 | P-S4 |
| **Incorrect** (one specific wrong claim) | I-S1 | I-S2 | I-S3 | I-S4 |

**Style rules:** content must stay equivalent across styles. Verbose adds restatement and filler, no new facts. Poor grammar changes wording only. Polished adds formal vocabulary only. Record token length as a covariate.

**Variant generation:** use an LLM that is *not* one of the judges. Check each variant against the content-equivalence checklist (same concepts present, same error present). Include a few real human-written answers as a reality check.

**Pilot size:** 20 questions × 12 variants = 240 answers.

**Judge runs per answer, per judge:** Rubric A at temperature 0 (1 run), Rubric B at temperature 0 (1 run), Rubric A at default temperature (3 runs) = 5 runs. With 3 judges, that is 3,600 calls.

**Judges:** 3 models from different families (for example a Gemini, a Llama via Groq, and a GPT or Claude model). Log exact model ID and date for each. One answer scored at a time.

**Phase 2 (only if the pilot works):** hedged vs overconfident tone, fake authoritative references, a bias-mitigation Rubric C, reasoning-before-score, ensembles, more questions, DSA domain.

## 4. Human labels

- Quality tier comes from the design and gives expected ordering, not exact scores.
- Two DBMS-literate raters score a **100-answer subset** (about 8 per cell, shuffled, blind to variant labels) using Rubric A.
- Report human-human QWK. Adjudicate disagreements of more than 1 point. Human consensus = mean or adjudicated score.
- Use only synthetic or consenting-volunteer content. Anonymize everything.

## 5. Metrics and analysis

| Question | Metrics |
|---|---|
| Agreement | QWK, ordinal Krippendorff's alpha, ICC, exact and adjacent agreement, MAE; Pearson/Spearman as supplements |
| Consistency | ICC across runs, SD per answer, share of answers with range ≥ 1 |
| Style and verbosity | Paired differences within quality level; Wilcoxon signed-rank with Holm correction; effect sizes; bootstrap CIs |
| Joint model | score ~ quality × style + log(length) + (1 | question) + (1 | judge) |
| Rubric sensitivity | Mean absolute difference A vs B; change in QWK versus humans |

Report everything relative to the human-human ceiling, since human agreement can be modest.

## 6. Pilot decision rule

Scale to 60-100 questions only if human-human QWK ≥ 0.60 and at least one style effect is measurable. Otherwise revise rubric anchors and re-pilot.

## 7. Threats to validity

LLM-written variants may be favored by same-family judges (self-preference, perplexity effects). Single domain, small pilot, and two raters. Model version drift. Rater length bias. Reference concepts shown to the judge may inflate agreement (consider a no-reference condition later).

## Appendix A. Judge prompt (fixed across conditions)

```
You are a computer science instructor grading a candidate's answer in a technical interview.
Question: {question}
Key concepts: {expected_concepts}
Rubric: {rubric}
Candidate answer: {answer}
Return only JSON: {"score": <integer 0-5>, "justification": "<max 2 sentences>"}
```

Score comes first in the JSON so the judge does not reason before scoring.

## Appendix B. Rubrics

**Anchors (shared):** 5 = fully correct, key concepts present, precise terms. 4 = correct, minor omission or imprecision. 3 = mostly correct, missing an important concept or one minor error. 2 = partial, significant gaps or one major error. 1 = mostly incorrect, fragments of relevant knowledge. 0 = incorrect, irrelevant, or empty.

**Rubric A (weighted):**
Score the answer on three criteria: Correctness (40%): are the technical claims accurate? Explanation (30%): is the reasoning clear and logically ordered? Completeness (30%): are the key concepts and important cases covered? Combine them into one 0-5 score using the anchors.

**Rubric B (prioritized):**
Judge primarily whether the answer is technically correct. Give secondary consideration to the clarity of the explanation and to whether the key concepts are covered. Give one 0-5 score using the anchors.

## Appendix C. 20 DBMS pilot questions

Difficulty: E easy, M medium, H hard. "Partial seed" is a concept to omit; "Incorrect seed" is a specific false claim to include.

| # | Diff | Question | Expected concepts | Partial seed (omit) | Incorrect seed |
|---|---|---|---|---|---|
| 1 | E | Primary key vs unique key? | PK identifies rows, one per table, no NULL; unique key allows several per table; NULL handling varies by DBMS; both enforce uniqueness | NULL handling and one-per-table | "A table can have many primary keys but one unique key" |
| 2 | E | DELETE vs TRUNCATE vs DROP? | DELETE removes rows with optional WHERE and fires triggers; TRUNCATE removes all rows, no WHERE, faster; DROP removes table structure and data | DROP removes the structure | "TRUNCATE accepts a WHERE clause" |
| 3 | E | INNER JOIN vs LEFT JOIN? | INNER returns matching rows only; LEFT returns all left rows, NULLs where no match | NULL fill | "LEFT JOIN returns all rows from both tables" |
| 4 | M | Explain ACID. | Atomicity, Consistency, Isolation, Durability, each with correct meaning | Isolation and consistency | "Isolation means committed data survives crashes" |
| 5 | M | Isolation levels and anomalies prevented? | Read uncommitted, read committed, repeatable read, serializable; dirty, non-repeatable, phantom reads | Mapping to anomalies | "Read committed prevents phantom reads" |
| 6 | M | What is a deadlock and how is it handled? | Circular wait on locks; detection via wait-for graph; prevention (lock ordering, timeouts); victim rollback | Handling methods | "Deadlock is reading uncommitted data" |
| 7 | M | Explain 1NF, 2NF, 3NF. | 1NF atomic values; 2NF no partial dependency; 3NF no transitive dependency | 2NF | "2NF removes transitive dependencies" |
| 8 | H | BCNF vs 3NF? | BCNF requires every determinant to be a candidate key; stricter than 3NF; may lose dependency preservation | Determinant condition | "BCNF is weaker than 3NF" |
| 9 | M | What is an index, and its trade-off? | Auxiliary structure (often B+ tree) speeds lookups and range scans; costs storage and slows writes | Write cost | "Indexes speed up reads and writes" |
| 10 | M | Clustered vs non-clustered index? | Clustered defines row order, one per table; non-clustered is a separate structure with row pointers, many allowed | One per table | "A table can have several clustered indexes" |
| 11 | H | Why B+ trees for indexes? | Balanced, high fanout, low height, few disk I/Os; linked leaves for range scans; hash suits equality only | Linked leaves / range scans | "B+ trees keep data in internal nodes" |
| 12 | M | WHERE vs HAVING? | WHERE filters rows before grouping; HAVING filters groups after aggregation and can use aggregates | Aggregates in HAVING | "WHERE runs after GROUP BY" |
| 13 | M | What is a view? | Stored query, virtual table; simplification and access control; materialized views store data; update limits | Uses and limits | "A view always stores a physical copy" |
| 14 | M | What is a trigger? | Runs automatically on INSERT/UPDATE/DELETE, before or after; auditing, integrity; hidden logic and debugging drawbacks | Drawbacks | "Triggers are called manually with CALL" |
| 15 | H | Write-ahead logging and crash recovery? | Log flushed before data pages; redo committed, undo uncommitted; checkpoints | Log-before-data rule | "WAL writes data pages before the log" |
| 16 | H | Optimistic vs pessimistic concurrency control? | Pessimistic locks first; optimistic validates at commit using versions or timestamps and aborts on conflict; fits low contention | One of the two | "Optimistic locking locks all rows at start" |
| 17 | H | What is the CAP theorem? | Under a network partition, choose consistency or availability; not all three guaranteed | The trade-off itself | "Enough replicas let you guarantee all three" |
| 18 | M | SQL vs NoSQL: when to use which? | Relational: schema, joins, ACID; NoSQL: flexible schema, horizontal scale, document/key-value/column/graph; depends on access pattern | One-sided view | "NoSQL cannot scale horizontally" |
| 19 | M | What is denormalization? | Deliberate redundancy to cut joins and speed reads; costs update anomalies and storage; read-heavy workloads | Costs | "Denormalization removes redundancy to improve consistency" |
| 20 | E | Foreign key vs primary key; referential integrity? | FK references a key in another table; enforces referential integrity; can be NULL and repeated; ON DELETE actions | Referential integrity | "A foreign key must be unique in its table" |

Verify each expected-concept list against your course material before freezing the dataset.
