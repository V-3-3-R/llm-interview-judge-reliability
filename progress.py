#!/usr/bin/env python3
"""Show how far the real judge run has got.
python progress.py results_raw/scores_real.csv frozen/answers_final.csv"""
import sys, pandas as pd
s = pd.read_csv(sys.argv[1]); a = pd.read_csv(sys.argv[2]); n = len(a); per = 7
print(f"Answers: {n}. Expected per judge: {n*per}. Total rows now: {len(s)}")
print(f"Duplicate keys (should be 0): {s.duplicated(['answer_id','judge','rubric','temperature','run']).sum()}")
g = s.groupby('judge').size().rename('done').to_frame(); g['expected'] = n*per; g['remaining'] = g.expected - g.done; g['percent'] = (100*g.done/g.expected).round(1)
print(g)
print("\nRows per judge and condition (each should reach", n, "):")
print(s.groupby(['judge','rubric','temperature','run']).size().unstack('judge').fillna(0).astype(int))
print("\nScore values seen (must be 0-5):", sorted(s.score.unique()))
