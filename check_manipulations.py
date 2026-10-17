#!/usr/bin/env python3
"""Manipulation checks for the answer dataset. Run before freezing:
python check_manipulations.py answers_v0.2_batch1.csv answer_key_v0.2_batch1.csv
Exit code 1 if any hard check fails."""
import csv, sys, collections
ans = {r["answer_id"]: r for r in csv.DictReader(open(sys.argv[1], encoding="utf-8"))}
key = list(csv.DictReader(open(sys.argv[2], encoding="utf-8")))
FUNC = {"about","each","and","the","of","to","by","in","a","an","that","is","with","for","from",
        "because","as","on","or","but","so","which","than","its","their","whereas","while"}
by_q = collections.defaultdict(dict)
for k in key:
    by_q[k["question_id"]][k["variant"]] = ans[k["answer_id"]]["answer"]
fails, warns = [], []
w = lambda s: len(s.split())
def need(cond, msg, hard=True):
    if not cond: (fails if hard else warns).append(msg)
for qid, v in sorted(by_q.items()):
    need(set(v) == {f"S{i}" for i in range(1, 9)}, f"{qid}: missing variants")
    if set(v) != {f"S{i}" for i in range(1, 9)}: continue
    s1 = w(v["S1"])
    need(w(v["S2"]) >= 2.5*s1, f"{qid}: S2 not >=2.5x S1 ({w(v['S2'])} vs {s1} words)")
    need(0.6 <= w(v["S3"])/s1 <= 1.3, f"{qid}: S3 length off ({w(v['S3'])} vs {s1})")
    need(0.7 <= w(v["S4"])/s1 <= 1.5, f"{qid}: S4 length off ({w(v['S4'])} vs {s1})")
    need(0.5 <= w(v["S6"])/s1 <= 1.6, f"{qid}: S6 length off ({w(v['S6'])} vs {s1})", hard=False)
    need(w(v["S7"]) <= w(v["S5"]), f"{qid}: S7 longer than S5", hard=False)
    need(w(v["S8"]) <= w(v["S6"]), f"{qid}: S8 longer than S6", hard=False)
    for s in ("S1","S3","S4","S5","S6","S7","S8"):
        t = v[s].strip()
        need(t[-1] in ".?!", f"{qid}-{s}: does not end with punctuation")
        need(t.rstrip(".?!").split()[-1].lower() not in FUNC, f"{qid}-{s}: ends on a dangling function word")
    need(len({v[s] for s in v}) == 8, f"{qid}: duplicate answers")
need(all(not any(t in a for t in ("CORRECT","S1","S2","partial","incorrect")) for a in ans), "IDs leak labels")
print(f"{len(by_q)} questions, {len(ans)} answers checked")
print("HARD FAILS:", len(fails)); [print("  -", m) for m in fails]
print("WARNINGS:", len(warns)); [print("  -", m) for m in warns]
sys.exit(1 if fails else 0)
