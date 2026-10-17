#!/usr/bin/env python3
"""Freeze the reviewed dataset. Run ONCE, after the human label review is finished.
python freeze_dataset.py data/answers_v0.2_reviewed.csv data/answer_key_v0.2_reviewed.csv
Creates frozen/answers_final.csv, frozen/answer_key_final.csv and frozen/FROZEN_MANIFEST.txt (SHA-256 fingerprints).
Refuses to run if the checks fail or if frozen files already exist."""
import sys, shutil, hashlib, subprocess, os, csv, datetime
ans, key = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
os.makedirs("frozen", exist_ok=True)
if os.path.exists("frozen/answers_final.csv"): sys.exit("frozen/answers_final.csv already exists: the dataset is already frozen. Do not overwrite.")
r = subprocess.run([sys.executable, os.path.join(here, "check_manipulations.py"), ans, key], capture_output=True, text=True)
print(r.stdout)
if r.returncode != 0: sys.exit("Checks failed. Fix the answers, then try again.")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
shutil.copy(ans, "frozen/answers_final.csv"); shutil.copy(key, "frozen/answer_key_final.csv")
n = sum(1 for _ in csv.DictReader(open("frozen/answers_final.csv", encoding="utf-8")))
with open("frozen/FROZEN_MANIFEST.txt", "w") as f:
    f.write(f"Dataset frozen: {datetime.datetime.now().isoformat(timespec='seconds')}\nAnswers: {n}\n")
    f.write(f"answers_final.csv SHA-256: {sha('frozen/answers_final.csv')}\nanswer_key_final.csv SHA-256: {sha('frozen/answer_key_final.csv')}\n")
    f.write("Do not edit these files after any judge has been run.\n")
print(open("frozen/FROZEN_MANIFEST.txt").read())
