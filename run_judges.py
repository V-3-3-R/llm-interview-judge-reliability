#!/usr/bin/env python3
"""Run LLM judges over answer variants (Protocol v0.1).

Per answer, per judge: Rubric A temp 0 (3 runs), Rubric B temp 0 (1 run),
Rubric A default temperature (3 runs) = 7 runs. Results are appended to a
long-format CSV after every call, so a crashed run can be resumed safely.

Usage:
  python run_judges.py --answers answers.csv --out scores.csv --dry-run --limit 5
  python run_judges.py --answers answers.csv --out scores.csv --judges gemini,groq_gptoss

Pacing and quota handling (does not change any request content, rubric, prompt or condition):
  each judge has a minimum interval between calls (min_interval below, override with --sleep);
  HTTP 429 waits for the server's Retry-After; if a daily quota is exhausted that judge is paused for
  this run and the others continue; --max-calls stops after N new scores; Ctrl+C is safe (progress is saved).
"""
import argparse, csv, json, os, random, re, sys, time
from datetime import datetime, timezone

import requests


def load_dotenv(path=".env"):
    """Optional: read KEY=VALUE lines from a local .env file (keeps keys out of the terminal history)."""
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_dotenv()

# ---- EDIT THESE: put the exact model ID you use, and record it in your paper ----
JUDGES = {
    "gemini": {"kind": "gemini", "model": "gemini-3.5-flash-lite", "key_env": "GEMINI_API_KEY", "min_interval": 4.0},
    "groq_gptoss": {"kind": "openai", "model": "openai/gpt-oss-20b", "key_env": "GROQ_API_KEY",
                    "base_url": "https://api.groq.com/openai/v1", "json_mode": True, "min_interval": 3.0},
    # Optional stronger third judge: replace SET_MODEL_ID, set OPENAI_API_KEY, add "gpt" to --judges
    "gpt": {"kind": "openai", "model": "SET_MODEL_ID", "key_env": "OPENAI_API_KEY",
            "base_url": "https://api.openai.com/v1", "json_mode": True, "min_interval": 1.0},
}

# (rubric, temperature, run). temperature None = provider default (not sent).
CONDITIONS = [("A", 0.0, 1), ("A", 0.0, 2), ("A", 0.0, 3), ("B", 0.0, 1), ("A", None, 1), ("A", None, 2), ("A", None, 3)]

ANCHORS = ("Anchors: 5 = fully correct, key concepts present, precise terms. "
           "4 = correct, minor omission or imprecision. "
           "3 = mostly correct, missing an important concept or one minor error. "
           "2 = partial, significant gaps or one major error. "
           "1 = mostly incorrect, fragments of relevant knowledge. "
           "0 = incorrect, irrelevant, or empty.")

RUBRICS = {
    "A": ("Score the answer on three criteria: Correctness (40%): are the technical claims accurate? "
          "Explanation (30%): is the reasoning clear and logically ordered? "
          "Completeness (30%): are the key concepts and important cases covered? "
          "Combine them into one 0-5 score. " + ANCHORS),
    "B": ("Judge primarily whether the answer is technically correct. Give secondary consideration "
          "to the clarity of the explanation and to whether the key concepts are covered. "
          "Give one 0-5 score. " + ANCHORS),
}

PROMPT = """You are a computer science instructor grading a candidate's answer in a technical interview.
Question: {question}
Key concepts: {expected_concepts}
Rubric: {rubric}
Candidate answer: {answer}
Return only JSON: {{"score": <integer 0-5>, "justification": "<max 2 sentences>"}}"""

OUT_FIELDS = ["answer_id", "judge", "model_id", "rubric", "temperature", "run",
              "score", "justification", "timestamp"]


def call_gemini(cfg, prompt, temp):
    gen = {"responseMimeType": "application/json"}
    if temp is not None:
        gen["temperature"] = temp
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{cfg['model']}:generateContent"
    r = requests.post(url, headers={"x-goog-api-key": os.environ[cfg["key_env"]]},
                      json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": gen},
                      timeout=90)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def call_openai(cfg, prompt, temp):
    body = {"model": cfg["model"], "messages": [{"role": "user", "content": prompt}]}
    if temp is not None:
        body["temperature"] = temp
    if cfg.get("json_mode"):
        body["response_format"] = {"type": "json_object"}
    r = requests.post(cfg["base_url"] + "/chat/completions",
                      headers={"Authorization": "Bearer " + os.environ[cfg["key_env"]]},
                      json=body, timeout=90)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


CALLERS = {"gemini": call_gemini, "openai": call_openai}


def parse(text):
    """Return (score:int, justification:str) or raise ValueError."""
    try:
        d = json.loads(text)
        score, just = int(d["score"]), str(d.get("justification", ""))
    except Exception:
        m = re.search(r'"score"\s*:\s*(\d)', text)
        if not m:
            raise ValueError("no score in: " + text[:120])
        score, just = int(m.group(1)), text[:200]
    if not 0 <= score <= 5:
        raise ValueError(f"score out of range: {score}")
    return score, just


def fake_call(row, rng):
    base = {"correct": 4.5, "partial": 2.5, "incorrect": 0.8}.get(row.get("quality", "").lower(), 2.5)
    s = max(0, min(5, round(base + rng.uniform(-1, 1))))
    return json.dumps({"score": s, "justification": "dry-run"})


class QuotaExhausted(Exception):
    pass


def retry_after_seconds(resp):
    ra = resp.headers.get("retry-after")
    if ra:
        try:
            return float(ra)
        except ValueError:
            pass
    m = re.search(r'"retryDelay"\s*:\s*"([\d.]+)s"', resp.text or "")
    return float(m.group(1)) if m else None


def is_daily_quota(resp):
    return bool(re.search(r"per day|PerDay|\bRPD\b|\bTPD\b|daily", resp.text or "", re.I))


def call_with_retry(fn, cfg, prompt, temp, tries=6):
    for i in range(tries):
        try:
            return fn(cfg, prompt, temp)
        except requests.HTTPError as e:
            code = e.response.status_code
            if code == 429:
                if is_daily_quota(e.response):
                    raise QuotaExhausted("daily quota exhausted")
                wait = retry_after_seconds(e.response)
                if wait is not None and wait > 180:
                    raise QuotaExhausted(f"server asks to wait {wait:.0f}s")
                if i < tries - 1:
                    time.sleep(min(max(wait or 0, 3 * 2 ** i) + 1, 180))
                    continue
                raise QuotaExhausted("rate limit persisted after retries")
            if code in (500, 502, 503) and i < tries - 1:
                time.sleep(2 ** i * 2)
                continue
            raise
        except requests.RequestException:
            if i < tries - 1:
                time.sleep(2 ** i * 2)
                continue
            raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--judges", default="gemini,groq_gptoss")
    ap.add_argument("--limit", type=int, default=0, help="only first N answers (testing)")
    ap.add_argument("--sleep", type=float, default=None, help="minimum seconds between calls to the same judge (default: per-judge min_interval)")
    ap.add_argument("--max-calls", type=int, default=0, help="stop after this many NEW scores (for daily quotas)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dry-run", action="store_true", help="no API calls; fake scores")
    args = ap.parse_args()

    with open(args.answers, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    need = {"answer_id", "question", "expected_concepts", "answer"}  # quality/style are NOT needed
    if not rows or not need <= set(rows[0]):
        sys.exit(f"answers CSV needs columns: {sorted(need)}")
    if args.limit:
        rows = rows[:args.limit]

    judges = [j.strip() for j in args.judges.split(",")]
    if not args.dry_run:
        for j in judges:
            cfg = JUDGES[j]
            if cfg["model"].startswith("SET_"):
                sys.exit(f"Set the model ID for '{j}' in JUDGES.")
            if cfg["key_env"] not in os.environ:
                sys.exit(f"Set environment variable {cfg['key_env']}.")

    done = set()
    exists = os.path.exists(args.out)
    if exists:
        with open(args.out, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                done.add((r["answer_id"], r["judge"], r["rubric"], r["temperature"], r["run"]))

    rng = random.Random(args.seed)
    order = rows[:]
    rng.shuffle(order)  # spreads any drift or rate limits across conditions

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    out = open(args.out, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(out, fieldnames=OUT_FIELDS)
    if not exists:
        w.writeheader()

    total = len(order) * len(judges) * len(CONDITIONS)
    n = failures = ok_calls = 0
    paused, last_call, per_judge_new = {}, {}, {j: 0 for j in judges}
    stop = False
    try:
        for row in order:
            if stop:
                break
            for j in judges:
                if stop:
                    break
                cfg = JUDGES[j]
                for rubric, temp, run in CONDITIONS:
                    n += 1
                    if j in paused:
                        continue
                    temp_label = "default" if temp is None else str(temp)
                    key = (row["answer_id"], j, rubric, temp_label, str(run))
                    if key in done:
                        continue
                    if args.max_calls and ok_calls >= args.max_calls:
                        stop = True
                        break
                    prompt = PROMPT.format(question=row["question"], rubric=RUBRICS[rubric],
                                           expected_concepts=row["expected_concepts"], answer=row["answer"])
                    try:
                        if args.dry_run:
                            text = fake_call(row, rng)
                        else:
                            gap = (args.sleep if args.sleep is not None else cfg.get("min_interval", 2.0)) - (time.monotonic() - last_call.get(j, -1e9))
                            if gap > 0:
                                time.sleep(gap)
                            try:
                                text = call_with_retry(CALLERS[cfg["kind"]], cfg, prompt, temp)
                            finally:
                                last_call[j] = time.monotonic()
                        score, just = parse(text)
                    except QuotaExhausted as e:
                        paused[j] = str(e)
                        print(f"[{n}/{total}] PAUSED judge '{j}' for this run: {e}. Other judges continue; rerun later to finish it.", file=sys.stderr)
                        if all(x in paused for x in judges):
                            stop = True
                            break
                        continue
                    except Exception as e:
                        failures += 1
                        print(f"[{n}/{total}] FAILED {key}: {e}", file=sys.stderr)
                        continue
                    w.writerow({"answer_id": row["answer_id"], "judge": j,
                                "model_id": "dry-run" if args.dry_run else cfg["model"],
                                "rubric": rubric, "temperature": temp_label, "run": run,
                                "score": score, "justification": just,
                                "timestamp": datetime.now(timezone.utc).isoformat()})
                    out.flush()
                    ok_calls += 1; per_judge_new[j] += 1
                    if ok_calls % 50 == 0:
                        print(f"[{n}/{total}] {ok_calls} new scores this run", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nStopped by user. All finished scores are saved; rerun the same command to resume.", file=sys.stderr)
    finally:
        out.close()
    remaining = len(order) * len(judges) * len(CONDITIONS) - len(done) - ok_calls
    print(f"Done for now. New scores this run: {ok_calls} {per_judge_new}. Failures: {failures}. "
          f"Remaining (all judges): {remaining}. Paused judges: {paused or 'none'}.", file=sys.stderr)


if __name__ == "__main__":
    main()
