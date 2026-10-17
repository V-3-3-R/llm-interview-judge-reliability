# Reliability of LLM-Based Technical Interview Evaluation: Agreement, Consistency, and Style Bias in Rubric-Based Grading

*Working title. Draft v0.1: Introduction complete; other sections are skeletons. Items in [brackets] are to be filled after the experiments.*

**Index Terms:** LLM-as-a-judge, automated interview evaluation, rubric-based grading, evaluation reliability, style bias, human-LLM agreement

---

## Paper structure (same path as the capstone paper)

| Capstone paper section | This paper | Action |
|---|---|---|
| Abstract, Index Terms | Abstract, Index Terms | Write last |
| I. Introduction (A Benefits, B Challenges, C Contributions) | I. Introduction (A Background, B Existing Evidence, C Research Gap, D Objective and Contributions, E Scope) | **Written below** |
| II. Literature Review (Table I comparison + text) | II. Literature Review (comparison table + 4 subsections) | Next |
| III. Methodology (system, architecture, framework, robustness) | III. Methodology (study design, dataset construction, rubrics and judge prompts, human rating, analysis plan) | After II |
| IV. Experimentation (hardware/software, data collection, implementation) | IV. Experimentation (API setup and judge settings, human rating collection, pipeline) | Hardware shrinks to a short note: API-based, no GPU |
| V. Results and Discussion | V. Results and Discussion (agreement, consistency, style bias, rubric sensitivity, cross-judge) | After data |
| VI. Conclusion | VI. Conclusion (findings, limitations, future work) | After data |
| References | References | Grows as we write |
| SHAP, ROC curves, confusion matrix, SMOTE | Not needed | **Skip** |

---

## I. INTRODUCTION

### A. Background

Large language models (LLMs) are now widely used as automated evaluators, an approach known as LLM-as-a-judge, in which a model is prompted either to score a response or to pick the better of two responses [1]. The practice follows a broader move away from reference-based text metrics such as BLEU and ROUGE toward model-based judgments that capture qualities such as coherence and informativeness [2]. Education shows the same trajectory. Automatic short answer grading (ASAG) has progressed from feature-based machine learning to pre-trained language models and, more recently, to LLMs [3], [4]. Interview assessment is a closely related setting. LLMs are being used to score interview responses in employment research [5], and interview-preparation tools increasingly give candidates automated feedback on their answers.

We use several terms throughout. **Pointwise scoring** means a judge assigns a score to one answer at a time, as opposed to comparing two answers. A **rubric** is a written set of criteria and score anchors given to the judge. **Agreement** is how closely judge scores match human scores, measured here with statistics suitable for ordinal scores such as weighted kappa. **Consistency** is how stable a judge's score is when the same answer is evaluated repeatedly or under small prompt changes. **Style bias** is a systematic change in score caused by how an answer is presented (for example its length, grammar, or formality) when its technical content has not changed.

### B. Existing Evidence

**Biases in LLM judges.** Early work on LLM judges identified position bias and verbosity bias [1]. Later studies broadened the picture. GPT-4 showed the strongest self-preference among eight judges, and judges favored text with lower perplexity [6]. A framework that quantifies 12 bias types found that advanced models still show significant biases in specific tasks [7]. Judges and humans can both be misled: human judges, like LLM judges, are vulnerable to perturbations such as fake references and length differences, to varying degrees [8]. Under pointwise scoring with a detailed rubric prompt, injected factual errors cut judge scores sharply while verbosity had little effect [9]. A comparison of nine debiasing strategies across five judges found that style bias, mostly favoring markdown over plain prose, was far larger than position bias, that verbosity bias differed by model, and that some debiasing strategies helped significantly [10].

**Rubric-based evaluation.** Rubrics are intended to make judgments more stable, but their reliability depends on the task. When LLMs designed and applied their own rubrics, agreement with human scores was high for dialogue data but fell to about 0.5 for news summarization and below 0.3 for biomedical summarization, where factual knowledge matters [2]. Several methods aim to improve rubric-based scoring: locking the rubric and grounding judgments in evidence [11], recursively decomposing and filtering rubric criteria [12], and open-source frameworks that combine ensembles, calibration, and psychometric reliability metrics [13]. Meta-evaluation of rubric-level judgments shows that judging remains far from reliable even for strong models [14]. A psychometric approach based on Item Response Theory separates a judge's intrinsic consistency from its human alignment [15], and a controlled-degradation approach tests whether judges rank artifacts of known quality in the right order, which raised alignment from below 0.7 to above 0.9 in some coding tasks [16].

**Grading of student and interview answers.** In short answer grading, traditional machine learning models outperformed GPT-4o on two datasets, and the most useful prompt components differed between English and Portuguese [4]. On real enterprise technical exams, zero-shot LLM baselines reached a quadratic weighted kappa of only about 0.36 to 0.38, compared with about 0.87 to 0.88 on LLM-generated exam data [17]. For employment interviews, a psychometric evaluation of LLM scoring found that ensembles of larger, newer models with detailed construct information can match or exceed single human raters, that lower temperature helped, and that LLM scores sometimes showed larger group differences than human ratings [5].

### C. Research Gap

Taken together, the evidence leaves four gaps. First, the most direct study of LLM interview scoring covers behavioral and personality-related constructs in employment selection and states that generalization to other constructs and contexts is unknown [5]; it does not examine whether LLM judges score the technical correctness of interview answers reliably. Second, most bias studies use pairwise comparisons or inject bias into otherwise strong answers, without human reference scores for technical answers of varying correctness [7], [9], [10]. Third, evidence on verbosity and style is mixed across studies and models [9], [10], and no study we reviewed crosses answer quality (correct, partial, incorrect) with presentation style while holding technical content fixed. Fourth, agreement with humans, repeat-run consistency, and rubric sensitivity are usually studied separately, so it is unclear how they relate for the same judges and answers. These statements reflect the studies we reviewed, not an exhaustive survey.

### D. Objective and Contributions

This study asks: **how reliably do LLM judges score technical interview answers against a fixed rubric, and how do answer style, rubric wording, and repeated runs change those scores when technical content is held constant?** We address five research questions.

- **RQ1 (Agreement):** How closely do LLM scores agree with human raters?
- **RQ2 (Consistency):** How stable are scores across repeated runs?
- **RQ3 (Style bias):** Does presentation style change scores when technical content is equivalent?
- **RQ4 (Rubric sensitivity):** Does rewording the rubric change agreement and scores?
- **RQ5 (Cross-judge):** Do different judges show different patterns of inconsistency and bias?

Our contributions are:

1. A controlled benchmark of 320 technical interview answers (40 questions across seven computing domains, 8 variants each) that crosses answer quality with presentation style, with human-verified labels.
2. An evaluation protocol that combines agreement, consistency, style-bias, and rubric-sensitivity analyses on the same answers and judges.
3. Empirical findings for [number] LLM judges compared with [number] independent human raters. [Fill after experiments.]
4. Released data and code for replication. [Confirm before submission.]

### E. Scope

The study is limited in the following ways.

- **Task:** pointwise scoring of short, text-only answers (about 15 to 95 words) on a 0 to 5 scale, in a practice (formative) setting. It does not address hiring decisions.
- **Content:** definitional and conceptual questions in seven domains (data structures and algorithms, databases, operating systems, networks, object-oriented design, machine learning, cloud and distributed systems). Coding exercises, system design, and spoken answers are out of scope.
- **Answers:** drafted by an LLM and then reviewed by humans, so they may be more regular than real candidate answers. Real candidate answers are not used.
- **Judges:** [number] API-accessed LLMs used without fine-tuning, with their exact model identifiers and run dates reported. Results may not carry to other models or later versions.
- **Human reference:** [number] independent raters scored a 100-answer subset using the same rubric as the judges.
- **Bias coverage:** length, grammar, and formality of wording. Other biases, including demographic fairness, are not tested.
- **Language:** English only.

---

## II. LITERATURE REVIEW *(skeleton)*

Table I: comparative review (Reference | Data or task | Approach | Key outcomes | Limitations or gaps), one row per study, plus a final row for the present study, as in the capstone paper.

- A. LLM-as-a-judge and its biases [1], [6]-[10]
- B. Rubric-based evaluation and reliability methods [2], [11]-[16]
- C. Automated grading of short answers and interviews [3]-[5], [17]
- D. Critical analysis and gaps (restates Section I-C with detail)

## III. METHODOLOGY *(skeleton)*

- A. Study design and variables (quality × style, judges, rubrics, temperature, runs)
- B. Dataset construction and validation (questions, 8 variants, manipulation checks, label review, freezing)
- C. Rubrics and judge prompt
- D. Human rating protocol (blind, independent, 100-answer subset)
- E. Analysis plan fixed before data collection (metrics, tests, exclusion rules)

## IV. EXPERIMENTATION *(skeleton)*

- A. Setup: API access, judge model identifiers, settings. Short note replacing the hardware section: no GPU was needed.
- B. Human rating collection (raters, dates, time taken)
- C. Implementation: pipeline, call counts, resumable runs

## V. RESULTS AND DISCUSSION *(after data)*

- A. Results: agreement, consistency, style bias, rubric sensitivity, cross-judge comparison
- B. Discussion and limitations

## VI. CONCLUSION *(after data)*

- A. Major findings
- B. Concluding remarks and future work

---

## REFERENCES

[1] L. Zheng *et al.*, "Judging LLM-as-a-judge with MT-Bench and Chatbot Arena," in *Advances in Neural Information Processing Systems (NeurIPS)*, 2023. arXiv:2306.05685.

[2] C. Siro, P. Aliannejadi, and M. Aliannejadi, "Learning to judge: LLMs designing and applying evaluation rubrics," arXiv:2602.08672, 2026.

[3] S. Burrows, I. Gurevych, and B. Stein, "The eras and trends of automatic short answer grading," *Int. J. Artificial Intelligence in Education*, vol. 25, pp. 60-117, 2015.

[4] R. Ferreira Mello *et al.*, "Automatic short answer grading in the LLM era: Does GPT-4 with prompt engineering beat traditional models?" in *Proc. 15th Int. Learning Analytics and Knowledge Conf. (LAK25)*, Dublin, Ireland, 2025, doi:10.1145/3706468.3706481.

[5] K. Stockdale, L. Hickman, and S. Liu, "Scoring employment interviews with large language models: Evaluation design components, validity investigations, and best practice recommendations," *J. Applied Psychology*, 2026 (accepted manuscript), doi:10.1037/apl0001396.

[6] K. Wataoka, T. Takahashi, and R. Ri, "Self-preference bias in LLM-as-a-judge," arXiv:2410.21819, 2024.

[7] J. Ye *et al.*, "Justice or prejudice? Quantifying biases in LLM-as-a-judge," arXiv:2410.02736, 2024.

[8] G. H. Chen, S. Chen, Z. Liu, F. Jiang, and B. Wang, "Humans or LLMs as the judge? A study on judgement bias," in *Proc. 2024 Conf. Empirical Methods in Natural Language Processing (EMNLP)*, 2024, pp. 8301-8327. arXiv:2402.10669.

[9] J. Gao *et al.*, "Evaluating and mitigating LLM-as-a-judge bias in communication systems," arXiv:2510.12462, 2026.

[10] S. K. Soumik, "Judging the judges: A systematic evaluation of bias mitigation strategies in LLM-as-a-judge pipelines," *Transactions on Machine Learning Research*, Jun. 2026. arXiv:2604.23178.

[11] Y. Hong *et al.*, "From rubrics to reliable scores: Evidence-grounded text evaluation with LLM judges," arXiv:2601.08654, 2026.

[12] W. F. Shen *et al.*, "Rethinking rubric generation for improving LLM judge and reward modeling for open-ended tasks," arXiv:2602.05125, 2026.

[13] D. Rao and C. Callison-Burch, "Autorubric: A unified framework for rubric-based LLM evaluation," arXiv:2603.00077, 2026.

[14] T. Pan *et al.*, "RubricEval: A rubric-level meta-evaluation benchmark for LLM judges in instruction following," arXiv:2603.25133, 2026.

[15] J. Choi *et al.*, "Diagnosing the reliability of LLM-as-a-judge via item response theory," arXiv:2602.00521, 2026.

[16] O. Fandina *et al.*, "Automated validation of LLM-based evaluators for software engineering artifacts," arXiv:2508.02827, 2025.

[17] F. Zhu *et al.*, "Towards human-like grading: A unified LLM-enhanced framework for subjective question evaluation," arXiv:2510.07912, 2025.

*Note: several references are preprints. Check each entry's final venue, year, and page numbers against the source before submission.*
