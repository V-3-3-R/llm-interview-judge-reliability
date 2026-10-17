#!/usr/bin/env python3
"""Analysis for the LLM-judge reliability study (Protocol v0.1 + dataset v0.2).
python analyze_results.py --scores scores_real.csv --key answer_key_final.csv --answers answers_final.csv \
       --human human_ratings_merged_4raters.csv --out results
Writes CSV tables, a bar chart and report.txt into the output folder."""
import argparse, os, itertools, warnings
import numpy as np, pandas as pd
from scipy.stats import wilcoxon, spearmanr, rankdata, binomtest
from sklearn.metrics import cohen_kappa_score
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
for a in ("scores", "key", "answers", "human", "out"): ap.add_argument("--" + a, required=True)
ap.add_argument("--boot", type=int, default=2000)
args = ap.parse_args(); os.makedirs(args.out, exist_ok=True)
rng = np.random.default_rng(42)
half_up = lambda x: np.floor(np.asarray(x, dtype=float) + 0.5).astype(int)
LAB = [0, 1, 2, 3, 4, 5]
qwk = lambda a, b: cohen_kappa_score(a, b, weights="quadratic", labels=LAB)
def icc21(X):
    X = np.asarray(X, float); n, k = X.shape; gm = X.mean()
    ms_r = k * ((X.mean(1) - gm) ** 2).sum() / (n - 1); ms_c = n * ((X.mean(0) - gm) ** 2).sum() / (k - 1)
    sse = ((X - X.mean(1, keepdims=True) - X.mean(0, keepdims=True) + gm) ** 2).sum(); ms_e = sse / ((n - 1) * (k - 1))
    d = ms_r + (k - 1) * ms_e + k * (ms_c - ms_e) / n
    return (ms_r - ms_e) / d if d else np.nan
def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); adj = np.empty_like(p); run = 0
    for rank, i in enumerate(o):
        run = max(run, (len(p) - rank) * p[i]); adj[i] = min(1, run)
    return adj
def boot_ci(stat_fn, n, reps):
    vals = [stat_fn(rng.integers(0, n, n)) for _ in range(reps)]
    return np.nanpercentile(vals, [2.5, 97.5])

S = pd.read_csv(args.scores); K = pd.read_csv(args.key); A = pd.read_csv(args.answers); H = pd.read_csv(args.human)
S["temperature"] = S.temperature.astype(str).str.replace(r"^0(\.0)?$", "0", regex=True)
A["words"] = A.answer.str.split().str.len(); A["log_words"] = np.log(A.words)
meta = K.merge(A[["answer_id", "words", "log_words"]], on="answer_id")
S = S.merge(meta, on="answer_id")
lines = []
def out(title, df, name):
    df.to_csv(os.path.join(args.out, name + ".csv"), index=False)
    lines.append("\n== " + title + " ==\n" + df.to_string(index=False)); print(lines[-1])

# ---------- human reference ----------
R = [c for c in H.columns if c.upper() in ("R1", "R2", "R3", "R4", "R5", "R6")]
H["h_mean"] = H[R].mean(axis=1); H["h_med"] = half_up(H[R].median(axis=1))
pair = [qwk(H[a], H[b]) for a, b in itertools.combinations(R, 2)]
loo = [qwk(H[r], half_up(H[[x for x in R if x != r]].median(axis=1))) for r in R]
ceil = pd.DataFrame([{"raters": len(R), "answers": len(H), "mean_pairwise_QWK": np.mean(pair), "min_pairwise_QWK": min(pair),
                      "mean_leave_one_out_QWK": np.mean(loo)}]).round(3)
out("Human ceiling (human-human agreement)", ceil, "0_human_ceiling")

# ---------- judge score sources ----------
def src(df, rub, temp, run=None):
    d = df[(df.rubric == rub) & (df.temperature == temp)]
    if run is not None: d = d[d.run == run]
    return d.groupby("answer_id").score.mean()
judges = sorted(S.judge.unique())
rows = []
for j in judges:
    dj = S[S.judge == j]
    sources = {"A_temp0_run1": src(dj, "A", "0", 1), "A_temp0_mean": src(dj, "A", "0"), "A_default_mean": src(dj, "A", "default"),
               "B_temp0_run1": src(dj, "B", "0", 1)}
    for name, s in sources.items():
        m = H.merge(s.rename("j"), left_on="answer_id", right_index=True)
        if m.empty: continue
        jr = half_up(m.j); n = len(m)
        ci = boot_ci(lambda i: qwk(jr[i], m.h_med.values[i]), n, args.boot)
        rows.append({"judge": j, "score_source": name, "n": n, "QWK_vs_human_median": qwk(jr, m.h_med), "QWK_CI_low": ci[0], "QWK_CI_high": ci[1],
                     "ICC21_vs_human_mean": icc21(np.c_[m.j, m.h_mean]), "exact": (jr == m.h_med).mean(),
                     "within1": (abs(jr - m.h_med) <= 1).mean(), "MAE_vs_human_mean": abs(m.j - m.h_mean).mean(),
                     "Spearman": spearmanr(m.j, m.h_mean)[0]})
out("RQ1 Agreement of each judge with the human reference (100-answer subset)", pd.DataFrame(rows).round(3), "1_agreement")

# ---------- consistency ----------
rows = []
for j in judges:
    dj = S[(S.judge == j) & (S.rubric == "A")]; flags = {}
    for t in ("0", "default"):
        W = dj[dj.temperature == t].pivot_table(index="answer_id", columns="run", values="score")
        if W.shape[1] < 2: continue
        W = W.dropna(); rg = W.max(axis=1) - W.min(axis=1); flags[t] = rg >= 1
        rows.append({"judge": j, "temperature": t, "answers": len(W), "runs": W.shape[1], "ICC21_across_runs": icc21(W.values),
                     "mean_SD_per_answer": W.std(axis=1).mean(), "share_range>=1": (rg >= 1).mean(), "share_range>=2": (rg >= 2).mean(),
                     "share_all_runs_identical": (rg == 0).mean()})
    if len(flags) == 2:
        both = pd.concat(flags, axis=1).dropna(); b = int(((both["default"]) & (~both["0"])).sum()); c = int(((~both["default"]) & (both["0"])).sum())
        p = binomtest(b, b + c, 0.5).pvalue if b + c else 1.0
        rows.append({"judge": j, "temperature": "H2 test default vs 0 (McNemar exact)", "answers": len(both), "runs": "", "ICC21_across_runs": "",
                     "mean_SD_per_answer": "", "share_range>=1": f"default-only={b}, t0-only={c}", "share_range>=2": f"p={p:.4f}", "share_all_runs_identical": ""})
out("RQ2 Consistency across repeated runs (Rubric A)", pd.DataFrame(rows).round(3), "2_consistency")

# ---------- variant means ----------
A_all = S[S.rubric == "A"].groupby(["judge", "answer_id"]).score.mean().rename("score").reset_index().merge(meta, on="answer_id")
vm = A_all.groupby(["judge", "variant"]).score.agg(["count", "mean", "std"]).reset_index().round(2)
hv = H.merge(K[["answer_id", "variant"]], on="answer_id").groupby("variant").h_mean.agg(["count", "mean", "std"]).reset_index().round(2)
hv.insert(0, "judge", "HUMAN (subset)"); vm = pd.concat([vm, hv])
out("Mean score by variant (judges: all Rubric A runs; humans: 4-rater mean on subset)", vm, "3_variant_means")

# ---------- style bias (paired by question) ----------
CON = [("S2", "S1", "verbose vs concise (correct)"), ("S3", "S1", "poor grammar vs concise (correct)"),
       ("S4", "S1", "polished jargon vs concise (correct)"), ("S5", "S7", "confident vs plain (partial)"),
       ("S6", "S8", "polished vs plain (incorrect)")]
rows = []
for j in judges:
    P = A_all[A_all.judge == j].pivot(index="question_id", columns="variant", values="score"); res = []
    for hi, lo, name in CON:
        d = (P[hi] - P[lo]).dropna().values; n = len(d)
        nz = d[d != 0]
        p = 1.0 if len(nz) == 0 else wilcoxon(nz).pvalue
        if len(nz):
            rk = rankdata(abs(nz)); rbc = (rk[nz > 0].sum() - rk[nz < 0].sum()) / rk.sum()
        else: rbc = 0.0
        ci = boot_ci(lambda i: d[i].mean(), n, args.boot)
        res.append({"judge": j, "contrast": name, "hi-lo": f"{hi}-{lo}", "n_questions": n, "mean_diff": d.mean(), "CI_low": ci[0], "CI_high": ci[1],
                    "rank_biserial": rbc, "p_wilcoxon": p})
    adj = holm([r["p_wilcoxon"] for r in res])
    for r, a in zip(res, adj): r["p_holm"] = a; rows.append(r)
out("RQ3 Style bias: paired score differences (Rubric A, Holm-corrected within judge)", pd.DataFrame(rows).round(4), "4_style_bias")

# ---------- rubric sensitivity ----------
rows = []
for j in judges:
    dj = S[S.judge == j]; a = src(dj, "A", "0", 1); b = src(dj, "B", "0", 1); m = pd.concat([a.rename("A"), b.rename("B")], axis=1).dropna()
    if m.empty: continue
    d = m.B - m.A; nz = d[d != 0]
    rows.append({"judge": j, "n": len(m), "mean_diff_B-A": d.mean(), "mean_abs_diff": d.abs().mean(), "share_differing": (d != 0).mean(),
                 "QWK_A_vs_B": qwk(half_up(m.A), half_up(m.B)), "p_wilcoxon": 1.0 if len(nz) == 0 else wilcoxon(nz).pvalue})
out("RQ4 Rubric sensitivity (temperature 0, run 1)", pd.DataFrame(rows).round(3), "5_rubric_sensitivity")

# ---------- cross-judge ----------
if len(judges) > 1:
    W = A_all.pivot(index="answer_id", columns="judge", values="score").dropna(); rows = []
    for a, b in itertools.combinations(judges, 2):
        rows.append({"judge_1": a, "judge_2": b, "n": len(W), "QWK": qwk(half_up(W[a]), half_up(W[b])), "Spearman": spearmanr(W[a], W[b])[0],
                     "mean_abs_diff": abs(W[a] - W[b]).mean()})
    out("RQ5 Cross-judge agreement (all 320 answers)", pd.DataFrame(rows).round(3), "6_cross_judge")

# ---------- mixed model ----------
try:
    import statsmodels.formula.api as smf
    txt = []
    for j in judges:
        df = A_all[A_all.judge == j].copy()
        m = smf.mixedlm("score ~ C(variant, Treatment('S1')) + log_words", df, groups=df["question_id"]).fit(reml=True)
        txt.append(f"--- {j} ---\n{m.summary().as_text()}")
    open(os.path.join(args.out, "7_mixed_models.txt"), "w").write("\n\n".join(txt)); lines.append("\n== Mixed models written to 7_mixed_models.txt ==")
except Exception as e:
    lines.append(f"\n(mixed model skipped: {e})")

# ---------- chart ----------
try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    V = [f"S{i}" for i in range(1, 9)]; fig, ax = plt.subplots(figsize=(9, 4)); groups = list(vm.judge.unique()); w = 0.8 / len(groups)
    for g, grp in enumerate(groups):
        d = vm[vm.judge == grp].set_index("variant").reindex(V)["mean"]; ax.bar(np.arange(8) + g * w, d.values, w, label=grp)
    ax.set_xticks(np.arange(8) + 0.4 - w / 2); ax.set_xticklabels(V); ax.set_ylabel("Mean score (0-5)"); ax.set_ylim(0, 5.3); ax.legend(fontsize=7)
    ax.set_title("Mean score by answer variant"); fig.tight_layout(); fig.savefig(os.path.join(args.out, "variant_means.png"), dpi=150)
except Exception as e:
    lines.append(f"(chart skipped: {e})")
open(os.path.join(args.out, "report.txt"), "w").write("\n".join(lines)); print("\nAll tables saved in", args.out)
