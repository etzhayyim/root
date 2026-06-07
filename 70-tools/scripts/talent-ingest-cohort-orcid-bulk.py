#!/usr/bin/env python3
"""
Talent — ORCID 2024 bulk country cohort ingest (ADR-0018 Tier 3 compliant).

Source: ORCID Public Data File 2024 (summaries)
  /Volumes/251220/orcid-2024/ORCID_2024_10_summaries.tar.gz
  License: CC0 1.0 Universal (public domain)
  Records: ~27.5M ORCID profiles

Method: regex streaming (12x faster than ElementTree on gzip-compressed tar)
  - Streams tar.gz without full extraction to disk
  - Extracts country codes with regex from employment/education/address sections
  - ~640 records/sec = ~12 hours for full 27.5M

ADR-0018 compliance: aggregate counts only — no ORCID iDs, names, or affiliations stored.

Output: vertex_talent_cohort rows, source=orcid-bulk
  isco_code = "2" (Professionals)
  country   = ISO-3166-1 alpha-2
  props     = JSON with emp/edu/addr breakdown

Progress: /tmp/orcid-bulk-progress.json (checkpoint every 500k records)

Usage:
  nohup python3 talent-ingest-cohort-orcid-bulk.py > /tmp/orcid-bulk.log 2>&1 &
  python3 talent-ingest-cohort-orcid-bulk.py --dry-run --limit 50000
"""
import argparse, json, os, re, sys, tarfile, time
from collections import defaultdict
from datetime import datetime, timezone

KOTOBA_URL   = os.environ.get("KOTOBA_URL", "postgresql://root@127.0.0.1:14566/dev?sslmode=disable")
DEFAULT_INPUT = "/Volumes/251220/orcid-2024/ORCID_2024_10_summaries.tar.gz"
TALENT_DID = "did:web:talent.etzhayyim.com"
SOURCE     = "orcid-bulk"
LICENSE    = "CC0"
HOMEPAGE   = "https://orcid.org/"
COLLECTION = "com.etzhayyim.apps.talent.talentCohort"
ISCO_CODE  = "2"
CHECKPOINT = "/tmp/orcid-bulk-progress.json"

# Match <common:country>XX</common:country> — only 2-letter uppercase codes
CC_RE = re.compile(rb'<common:country>([A-Z]{2})</common:country>')

# Section boundary markers (bytes)
EMPLOYMENT_START = b'<activities:employments'
EMPLOYMENT_END   = b'</activities:employments>'
EDUCATION_START  = b'<activities:educations'
EDUCATION_END    = b'</activities:educations>'
ADDRESSES_START  = b'<address:addresses'
ADDRESSES_END    = b'</address:addresses>'

def extract_section_countries(data, start_marker, end_marker):
    start = data.find(start_marker)
    if start < 0:
        return set()
    end = data.find(end_marker, start)
    if end < 0:
        end = len(data)
    section = data[start:end]
    return {m.group(1).decode() for m in CC_RE.finditer(section)}

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input",    default=DEFAULT_INPUT)
    p.add_argument("--dry-run",  action="store_true")
    p.add_argument("--year",     default="2024")
    p.add_argument("--limit",    type=int, default=0)
    return p.parse_args()

def stream_counts(input_path, limit):
    emp_counts  = defaultdict(int)
    edu_counts  = defaultdict(int)
    addr_counts = defaultdict(int)
    total = 0
    errors = 0
    t0 = time.time()

    with tarfile.open(input_path, "r:gz") as tar:
        for member in tar:
            if not member.name.endswith(".xml"):
                continue
            f = tar.extractfile(member)
            if f is None:
                continue
            try:
                data = f.read()
                for cc in extract_section_countries(data, EMPLOYMENT_START, EMPLOYMENT_END):
                    emp_counts[cc] += 1
                for cc in extract_section_countries(data, EDUCATION_START, EDUCATION_END):
                    edu_counts[cc] += 1
                for cc in extract_section_countries(data, ADDRESSES_START, ADDRESSES_END):
                    addr_counts[cc] += 1
                total += 1
            except Exception:
                errors += 1
                continue

            if total % 500_000 == 0:
                elapsed = time.time() - t0
                rate = total / elapsed if elapsed > 0 else 0
                eta  = (27_500_000 - total) / rate if rate > 0 else 0
                print(
                    f"[orcid-bulk] {total:>10,}  "
                    f"emp_cc={len(emp_counts)}  "
                    f"rate={rate:.0f}/s  "
                    f"eta={eta/3600:.1f}h",
                    flush=True,
                )
                with open(CHECKPOINT, "w") as cp:
                    json.dump({
                        "processed":    total,
                        "errors":       errors,
                        "emp_countries": len(emp_counts),
                        "top_emp":      sorted(emp_counts.items(), key=lambda x: -x[1])[:30],
                        "elapsed_h":    round(elapsed / 3600, 2),
                    }, cp, indent=2)

            if limit > 0 and total >= limit:
                break

    return emp_counts, edu_counts, addr_counts, total, errors

def build_rows(emp_counts, edu_counts, addr_counts, year, now_iso):
    rows = []
    all_cc = set(emp_counts) | set(edu_counts) | set(addr_counts)
    for cc in sorted(all_cc):
        emp  = emp_counts.get(cc, 0)
        edu  = edu_counts.get(cc, 0)
        addr = addr_counts.get(cc, 0)
        count = emp if emp > 0 else (edu if edu > 0 else addr)
        if count == 0:
            continue
        vid  = f"cohort:orcid-bulk:{year}:{ISCO_CODE}:{cc}:SEX_T:{year}"
        rkey = f"orcid-bulk-{year}-{ISCO_CODE}-{cc}-SEX_T-{year}"
        rows.append((
            vid, rkey, TALENT_DID, COLLECTION, SOURCE, LICENSE, HOMEPAGE,
            ISCO_CODE, cc, "SEX_T", year,
            count / 1000,
            "thousands", now_iso,
        ))
    return rows

def insert_rows(rows, dry_run):
    if dry_run or not rows:
        return
    import psycopg2
    conn = psycopg2.connect(KOTOBA_URL)
    cur  = conn.cursor()
    cols = ("vertex_id","rkey","repo","label","source","source_license","source_homepage",
            "isco_code","country","sex","time_period","size_thousands","unit","ingested_at")
    placeholders = ",".join([f"({','.join(['%s']*len(cols))})"] * len(rows))
    flat = [v for row in rows for v in row]
    cur.execute(
        f"INSERT INTO vertex_talent_cohort ({','.join(cols)}) VALUES {placeholders}",
        flat,
    )
    conn.commit()
    cur.close()
    conn.close()
    print(f"[orcid-bulk] inserted {len(rows)} rows", flush=True)

def main():
    args = parse_args()
    print(f"[orcid-bulk] input={args.input}  dry-run={args.dry_run}  year={args.year}  limit={args.limit or 'all'}",
          flush=True)
    if not os.path.exists(args.input):
        print(f"error: not found: {args.input}"); sys.exit(1)

    t0 = time.time()
    emp_counts, edu_counts, addr_counts, total, errors = stream_counts(args.input, args.limit)
    elapsed = time.time() - t0

    print(f"[orcid-bulk] done: total={total:,}  errors={errors}  elapsed={elapsed/3600:.2f}h", flush=True)

    top = sorted(emp_counts.items(), key=lambda x: -x[1])[:30]
    print("[orcid-bulk] top 30 employment countries:")
    for cc, n in top:
        print(f"  {cc}: {n:,}")

    now_iso = datetime.now(timezone.utc).isoformat()
    rows = build_rows(emp_counts, edu_counts, addr_counts, args.year, now_iso)
    print(f"[orcid-bulk] {len(rows)} cohort rows", flush=True)

    insert_rows(rows, args.dry_run)

    summary = {
        "source": SOURCE, "year": args.year, "dry_run": args.dry_run,
        "total_profiles": total, "errors": errors,
        "emp_countries": len(emp_counts), "edu_countries": len(edu_counts),
        "rows_written": 0 if args.dry_run else len(rows),
        "top_emp_30": top,
        "elapsed_hours": round(elapsed / 3600, 2),
    }
    with open(CHECKPOINT, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[orcid-bulk] checkpoint: {CHECKPOINT}")

if __name__ == "__main__":
    main()
