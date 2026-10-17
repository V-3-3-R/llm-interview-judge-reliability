#!/usr/bin/env python3
"""Pre-specified sensitivity analysis plus follow-up checks (run AFTER analyze_results.py).
python extra_analysis.py --scores results_raw/scores_real.csv --key frozen/answer_key_final.csv \
       --answers frozen/answers_final.csv --human human_rating/human_ratings_merged_4raters.csv --out results_extra
PRE-SPECIFIED (Protocol/Section III-E): (2) sensitivity analysis without the 14 borderline partial answers.
EXPLORATORY (label them so in the paper): everything else (matched-subset means, mid-range agreement,
errors by quality, paired bootstrap differences, style contrasts by rubric/temperature, confusion matrices)."""
import argparse, os, itertools, warnings
import numpy as np, pandas as pd
from scipy.stats import wilcoxon, rankdata
from sklearn.metrics import cohen_kappa_score
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
for a in ("scores", "key", "answers", "human", "out"): ap.add_argument("--" + a, required=True)
ap.add_argument("--boot", type=int, default=2000)
args = ap.parse_args(); os.makedirs(args.out, exist_ok=True)
rng = np.random.default_rng(7)
half_up = lambda x: np.floor(np.asarray(x, float) + 0.5).astype(int)
qwk = lambda a, b: cohen_kappa_score(a, b, weights="quadratic", labels=[0, 1, 2, 3, 4, 5])
def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); adj = np.empty_like(p); run = 0
    for rank, i in enumerate(o): run = max(run, (len(p) - rank) * p[i]); adj[i] = min(1, run)
    return adj
def ci(fn, n, reps): return np.nanpercentile([fn(rng.integers(0, n, n)) for _ in range(reps)], [2.5, 97.5])

S = pd.read_csv(args.scores); K = pd.read_csv(args.key); H = pd.read_csv(args.human)
S["temperature"] = S.temperature.astype(str).str.replace(r"^0(\.0)?$", "0", regex=True)
R = [c for c in H.columns if c.upper() in ("R1", "R2", "R3", "R4", "R5", "R6")]
H["h_mean"] = H[R].mean(axis=1); H["h_med"] = half_up(H[R].median(axis=1))
H = H.merge(K[["answer_id", "variant", "quality", "question_id", "review_flag"]], on="answer_id")
flag_ids = set(K.loc[K.review_flag.notna() & (K.review_flag.astype(str) != ""), "answer_id"])
flag_q = set(K.loc[K.answer_id.isin(flag_ids), "question_id"])
judges = sorted(S.judge.unique()); lines = []
def out(title, df, name):
    df.to_csv(os.path.join(args.out, name + ".csv"), index=False); lines.append("\n== " + title + " ==\n" + df.to_string(index=False)); print(lines[-1])
SRC = {"A_temp0_run1": ("A", "0", 1), "A_temp0_mean": ("A", "0", None), "A_default_mean": ("A", "default", None), "B_temp0_run1": ("B", "0", 1)}
def score(j, src):
    r, t, run = SRC[src]; d = S[(S.judge == j) & (S.rubric == r) & (S.temperature == t)]
    if run is not None: d = d[d.run == run]
    return d.groupby("answer_id").score.mean()
A_all = {j: S[(S.judge == j) & (S.rubric == "A")].groupby("answer_id").score.mean() for j in judges}

# 1 matched-subset means (exploratory)
rows = []
for j in judges:
    m = H.assign(j=H.answer_id.map(A_all[j]))
    for v, g in m.groupby("variant"):
        rows.append({"judge": j, "variant": v, "n": len(g), "human_mean": g.h_mean.mean(), "judge_mean": g.j.mean(), "judge_minus_human": g.j.mean() - g.h_mean.mean()})
out("EXPLORATORY 1. Judge versus human mean on the SAME 100 rated answers, by variant", pd.DataFrame(rows).round(2), "1_matched_subset_means")

# 2 PRE-SPECIFIED sensitivity
def contrasts(sc, exclude_q=()):
    meta = K.assign(s=K.answer_id.map(sc)); P = meta.pivot(index="question_id", columns="variant", values="s")
    P = P.drop(index=[q for q in exclude_q if q in P.index]); res = []
    for hi, lo, name in [("S2", "S1", "verbose vs concise"), ("S3", "S1", "poor grammar vs concise"), ("S4", "S1", "polished jargon vs concise"),
                         ("S5", "S7", "confident vs plain (partial)"), ("S6", "S8", "polished vs plain (incorrect)")]:
        d = (P[hi] - P[lo]).dropna().values; nz = d[d != 0]; n = len(d)
        p = 1.0 if len(nz) == 0 else wilcoxon(nz).pvalue
        c = ci(lambda i: d[i].mean(), n, args.boot)
        res.append({"contrast": name, "hi-lo": f"{hi}-{lo}", "n_questions": n, "mean_diff": d.mean(), "CI_low": c[0], "CI_high": c[1], "p_wilcoxon": p})
    for r, a in zip(res, holm([r["p_wilcoxon"] for r in res])): r["p_holm"] = a
    return pd.DataFrame(res)
rows = []
for j in judges:
    d = contrasts(A_all[j], flag_q); d.insert(0, "judge", j); rows.append(d)
out(f"PRE-SPECIFIED 2a. Style contrasts WITHOUT the {len(flag_q)} borderline questions ({sorted(flag_q)}), Rubric A all runs", pd.concat(rows).round(4), "2a_sensitivity_style_contrasts")
rows = []
for j in judges:
    for src in SRC:
        s = score(j, src); m = H[~H.answer_id.isin(flag_ids)].assign(j=lambda d: d.answer_id.map(s)).dropna(subset=["j"]); jr = half_up(m.j)
        c = ci(lambda i: qwk(jr[i], m.h_med.values[i]), len(m), args.boot)
        rows.append({"judge": j, "score_source": src, "n": len(m), "QWK": qwk(jr, m.h_med), "CI_low": c[0], "CI_high": c[1], "exact": (jr == m.h_med).mean(), "MAE_vs_human_mean": abs(m.j - m.h_mean).mean()})
out("PRE-SPECIFIED 2b. Agreement WITHOUT the borderline human-rated answers", pd.DataFrame(rows).round(3), "2b_sensitivity_agreement")

# 3 mid-range agreement (exploratory)
mid = H[(H.h_mean >= 1.5) & (H.h_mean <= 4.5)]; rows = []
pw_ex = np.mean([(mid[a] == mid[b]).mean() for a, b in itertools.combinations(R, 2)])
rows.append({"judge": "HUMAN pairs", "score_source": "mean pairwise", "n": len(mid), "QWK": np.mean([qwk(mid[a], mid[b]) for a, b in itertools.combinations(R, 2)]), "exact": pw_ex, "within1": np.mean([((mid[a] - mid[b]).abs() <= 1).mean() for a, b in itertools.combinations(R, 2)]), "MAE_vs_human_mean": np.nan})
for j in judges:
    for src in SRC:
        m = mid.assign(j=mid.answer_id.map(score(j, src))); jr = half_up(m.j)
        rows.append({"judge": j, "score_source": src, "n": len(m), "QWK": qwk(jr, m.h_med), "exact": (jr == m.h_med).mean(), "within1": (abs(jr - m.h_med) <= 1).mean(), "MAE_vs_human_mean": abs(m.j - m.h_mean).mean()})
out("EXPLORATORY 3. Agreement on the mid-range answers only (human mean 1.5 to 4.5)", pd.DataFrame(rows).round(3), "3_midrange_agreement")

# 4 error by quality
rows = []
for j in judges:
    for src in ("A_temp0_run1", "B_temp0_run1"):
        m = H.assign(j=H.answer_id.map(score(j, src)))
        for q, g in m.groupby("quality"):
            rows.append({"judge": j, "score_source": src, "quality": q, "n": len(g), "mean_signed_error(judge-human)": (g.j - g.h_mean).mean(), "MAE": (g.j - g.h_mean).abs().mean()})
out("EXPLORATORY 4. Judge error by design quality (rated answers)", pd.DataFrame(rows).round(3), "4_error_by_quality")

# 5 paired bootstrap differences
rows = []
def pair_diff(fa, fb, label):
    m = H.copy(); a = half_up(m.answer_id.map(fa)); b = half_up(m.answer_id.map(fb)); h = m.h_med.values
    f = lambda i: qwk(a[i], h[i]) - qwk(b[i], h[i]); d = f(np.arange(len(m))); c = ci(f, len(m), args.boot)
    rows.append({"comparison": label, "QWK_difference": d, "CI_low": c[0], "CI_high": c[1]})
for j in judges: pair_diff(score(j, "B_temp0_run1"), score(j, "A_temp0_run1"), f"{j}: Rubric B minus Rubric A (temp 0, run 1)")
if len(judges) > 1:
    for src in ("A_temp0_run1", "B_temp0_run1"): pair_diff(score(judges[0], src), score(judges[1], src), f"{judges[0]} minus {judges[1]} ({src})")
out("EXPLORATORY 5. Paired bootstrap of QWK differences against the human median", pd.DataFrame(rows).round(3), "5_paired_differences")

# 6 style contrasts by rubric/temperature
rows = []
for j in judges:
    for src in ("A_temp0_mean", "A_default_mean", "B_temp0_run1"):
        d = contrasts(score(j, src)); d.insert(0, "score_source", src); d.insert(0, "judge", j); rows.append(d)
out("EXPLORATORY 6. Style contrasts by rubric and temperature (all 40 questions)", pd.concat(rows).round(4), "6_style_by_condition")

# 7 confusion matrices
rows = []
for j in judges:
    for src in ("A_temp0_run1", "B_temp0_run1"):
        m = H.assign(j=half_up(H.answer_id.map(score(j, src)))); ct = pd.crosstab(m.h_med, m.j).reindex(index=range(6), columns=range(6), fill_value=0)
        ct.insert(0, "human_median", ct.index); ct.insert(0, "score_source", src); ct.insert(0, "judge", j); rows.append(ct)
out("EXPLORATORY 7. Confusion matrices (rows: human median; columns: judge score)", pd.concat(rows), "7_confusion")
open(os.path.join(args.out, "report_extra.txt"), "w").write("\n".join(lines)); print("\nSaved in", args.out)
