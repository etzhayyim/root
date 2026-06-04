#!/usr/bin/env python3
"""
Emit one stateProfile JSON + N stateProcedure JSONs + N stateDocument JSONs
per country under 60-apps/etzhayyim-project-states/data/gov/{iso3}/, ready for
PDS bulk putRecord.

Usage:
    python3 emit-state-records.py               # emit all
    python3 emit-state-records.py --iso jpn,usa # emit specified
    python3 emit-state-records.py --out /tmp/state-records

Output layout:
    {out}/profile/{iso3}.json
    {out}/procedure/{iso3}-{slug}.json
    {out}/document/{iso3}-{slug}.json

Each file is a ready-to-POST body for /xrpc/com.atproto.repo.putRecord.
"""
import argparse, json, os, sys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "60-apps/etzhayyim-project-states/data/gov"
REPO = "states.etzhayyim.com"

# ISO3 → (name, region) extracted from seed_domains.go sovereignSeeds()
COUNTRY = {
    "jpn":("Japan","east_asia"),"chn":("China","east_asia"),"kor":("South Korea","east_asia"),
    "prk":("North Korea","east_asia"),"mng":("Mongolia","east_asia"),
    "idn":("Indonesia","southeast_asia"),"tha":("Thailand","southeast_asia"),"sgp":("Singapore","southeast_asia"),
    "mys":("Malaysia","southeast_asia"),"phl":("Philippines","southeast_asia"),"vnm":("Vietnam","southeast_asia"),
    "mmr":("Myanmar","southeast_asia"),"khm":("Cambodia","southeast_asia"),"lao":("Laos","southeast_asia"),
    "brn":("Brunei","southeast_asia"),"tls":("Timor-Leste","southeast_asia"),
    "ind":("India","south_asia"),"pak":("Pakistan","south_asia"),"bgd":("Bangladesh","south_asia"),
    "lka":("Sri Lanka","south_asia"),"npl":("Nepal","south_asia"),"btn":("Bhutan","south_asia"),
    "mdv":("Maldives","south_asia"),"afg":("Afghanistan","south_asia"),
    "kaz":("Kazakhstan","central_asia"),"uzb":("Uzbekistan","central_asia"),"tkm":("Turkmenistan","central_asia"),
    "kgz":("Kyrgyzstan","central_asia"),"tjk":("Tajikistan","central_asia"),
    "tur":("Turkey","western_asia"),"sau":("Saudi Arabia","western_asia"),"are":("UAE","western_asia"),
    "isr":("Israel","western_asia"),"irn":("Iran","western_asia"),"irq":("Iraq","western_asia"),
    "jor":("Jordan","western_asia"),"lbn":("Lebanon","western_asia"),"syr":("Syria","western_asia"),
    "yem":("Yemen","western_asia"),"omn":("Oman","western_asia"),"kwt":("Kuwait","western_asia"),
    "qat":("Qatar","western_asia"),"bhr":("Bahrain","western_asia"),"pse":("Palestine","western_asia"),
    "cyp":("Cyprus","western_asia"),"geo":("Georgia","western_asia"),"arm":("Armenia","western_asia"),
    "aze":("Azerbaijan","western_asia"),
    "gbr":("United Kingdom","western_europe"),"fra":("France","western_europe"),"deu":("Germany","western_europe"),
    "che":("Switzerland","western_europe"),"nld":("Netherlands","western_europe"),"bel":("Belgium","western_europe"),
    "aut":("Austria","western_europe"),"irl":("Ireland","western_europe"),"lux":("Luxembourg","western_europe"),
    "mco":("Monaco","western_europe"),"lie":("Liechtenstein","western_europe"),"and":("Andorra","western_europe"),
    "swe":("Sweden","northern_europe"),"nor":("Norway","northern_europe"),"fin":("Finland","northern_europe"),
    "dnk":("Denmark","northern_europe"),"isl":("Iceland","northern_europe"),"est":("Estonia","northern_europe"),
    "lva":("Latvia","northern_europe"),"ltu":("Lithuania","northern_europe"),
    "ita":("Italy","southern_europe"),"esp":("Spain","southern_europe"),"prt":("Portugal","southern_europe"),
    "grc":("Greece","southern_europe"),"hrv":("Croatia","southern_europe"),"svn":("Slovenia","southern_europe"),
    "mlt":("Malta","southern_europe"),"smr":("San Marino","southern_europe"),"vat":("Vatican City","southern_europe"),
    "mne":("Montenegro","southern_europe"),"mkd":("North Macedonia","southern_europe"),
    "pol":("Poland","eastern_europe"),"rou":("Romania","eastern_europe"),"hun":("Hungary","eastern_europe"),
    "cze":("Czech Republic","eastern_europe"),"svk":("Slovakia","eastern_europe"),"ukr":("Ukraine","eastern_europe"),
    "blr":("Belarus","eastern_europe"),"bgr":("Bulgaria","eastern_europe"),"srb":("Serbia","eastern_europe"),
    "bih":("Bosnia and Herzegovina","eastern_europe"),"alb":("Albania","eastern_europe"),
    "rus":("Russia","eastern_europe"),
    "usa":("United States","north_america"),"can":("Canada","north_america"),"mex":("Mexico","north_america"),
    "gtm":("Guatemala","central_america"),"hnd":("Honduras","central_america"),"slv":("El Salvador","central_america"),
    "nic":("Nicaragua","central_america"),"cri":("Costa Rica","central_america"),"pan":("Panama","central_america"),
    "blz":("Belize","central_america"),
    "cub":("Cuba","caribbean"),"dom":("Dominican Republic","caribbean"),"hti":("Haiti","caribbean"),
    "jam":("Jamaica","caribbean"),"bhs":("Bahamas","caribbean"),"brb":("Barbados","caribbean"),
    "atg":("Antigua and Barbuda","caribbean"),"dma":("Dominica","caribbean"),"grd":("Grenada","caribbean"),
    "lca":("Saint Lucia","caribbean"),"vct":("Saint Vincent and the Grenadines","caribbean"),
    "kna":("Saint Kitts and Nevis","caribbean"),"tto":("Trinidad and Tobago","caribbean"),
    "bra":("Brazil","south_america"),"arg":("Argentina","south_america"),"col":("Colombia","south_america"),
    "chl":("Chile","south_america"),"per":("Peru","south_america"),"ven":("Venezuela","south_america"),
    "ecu":("Ecuador","south_america"),"bol":("Bolivia","south_america"),"pry":("Paraguay","south_america"),
    "ury":("Uruguay","south_america"),"guy":("Guyana","south_america"),"sur":("Suriname","south_america"),
    "aus":("Australia","oceania"),"nzl":("New Zealand","oceania"),"fji":("Fiji","oceania"),
    "png":("Papua New Guinea","oceania"),"slb":("Solomon Islands","oceania"),"vut":("Vanuatu","oceania"),
    "wsm":("Samoa","oceania"),"ton":("Tonga","oceania"),"kir":("Kiribati","oceania"),
    "fsm":("Micronesia","oceania"),"mhl":("Marshall Islands","oceania"),"plw":("Palau","oceania"),
    "tuv":("Tuvalu","oceania"),"nru":("Nauru","oceania"),
    "egy":("Egypt","northern_africa"),"dza":("Algeria","northern_africa"),"mar":("Morocco","northern_africa"),
    "tun":("Tunisia","northern_africa"),"lby":("Libya","northern_africa"),"sdn":("Sudan","northern_africa"),
    "ssd":("South Sudan","northern_africa"),
    "nga":("Nigeria","west_africa"),"gha":("Ghana","west_africa"),"civ":("Cote d'Ivoire","west_africa"),
    "sen":("Senegal","west_africa"),"mli":("Mali","west_africa"),"bfa":("Burkina Faso","west_africa"),
    "ner":("Niger","west_africa"),"gin":("Guinea","west_africa"),"sle":("Sierra Leone","west_africa"),
    "lbr":("Liberia","west_africa"),"tgo":("Togo","west_africa"),"ben":("Benin","west_africa"),
    "gmb":("Gambia","west_africa"),"gnb":("Guinea-Bissau","west_africa"),"cpv":("Cabo Verde","west_africa"),
    "mrt":("Mauritania","west_africa"),
    "ken":("Kenya","east_africa"),"eth":("Ethiopia","east_africa"),"tza":("Tanzania","east_africa"),
    "uga":("Uganda","east_africa"),"rwa":("Rwanda","east_africa"),"bdi":("Burundi","east_africa"),
    "som":("Somalia","east_africa"),"eri":("Eritrea","east_africa"),"dji":("Djibouti","east_africa"),
    "com":("Comoros","east_africa"),"syc":("Seychelles","east_africa"),
    "cod":("DR Congo","central_africa"),"cog":("Republic of the Congo","central_africa"),
    "cmr":("Cameroon","central_africa"),"gab":("Gabon","central_africa"),"gnq":("Equatorial Guinea","central_africa"),
    "caf":("Central African Republic","central_africa"),"tcd":("Chad","central_africa"),
    "stp":("Sao Tome and Principe","central_africa"),
    "zaf":("South Africa","southern_africa"),"ago":("Angola","southern_africa"),"moz":("Mozambique","southern_africa"),
    "zmb":("Zambia","southern_africa"),"zwe":("Zimbabwe","southern_africa"),"bwa":("Botswana","southern_africa"),
    "nam":("Namibia","southern_africa"),"mwi":("Malawi","southern_africa"),"lso":("Lesotho","southern_africa"),
    "swz":("Eswatini","southern_africa"),
    "mdg":("Madagascar","east_africa"),
    "twn":("Taiwan","east_asia"),"xkx":("Kosovo","eastern_europe"),
}

STATIC_PATH = Path(__file__).parent / "static-profile-data.json"
STATIC = json.loads(STATIC_PATH.read_text()) if STATIC_PATH.exists() else {}

def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:48] or "x"

def read_ndjson(path):
    if not path.exists() or path.stat().st_size == 0: return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line: continue
        try: out.append(json.loads(line))
        except: pass
    return out

def put_body(collection, rkey, record):
    return {"repo": REPO, "collection": collection, "rkey": rkey, "record": record}

def emit_country(iso3, out_dir):
    if iso3 not in COUNTRY: return (0, 0, 0)
    name, region = COUNTRY[iso3]
    cdir = DATA_DIR / iso3
    ministries = read_ndjson(cdir / "ministry.ndjson")
    contracts = read_ndjson(cdir / "contract.ndjson")
    bpmn_dir = cdir / "bpmn"
    bpmn_files = sorted([f.name for f in bpmn_dir.glob("*.bpmn")]) if bpmn_dir.exists() else []

    # Build inline procedures (top 6 ministries with BPMN or website)
    inline_procedures = []
    for m in ministries[:6]:
        path = m.get("path") or slug(m.get("name", ""))
        if not path: continue
        bpmn_name = path.replace(":", "-") + ".bpmn"
        has_bpmn = bpmn_name in bpmn_files
        inline_procedures.append({
            "id": f"{iso3}.{slug(path)}",
            "title": m.get("nameEn") or m.get("name", ""),
            "titleLocal": m.get("name", ""),
            "authority": m.get("name", ""),
            "basis": m.get("contract", ""),
            "portalUri": m.get("website", ""),
            "bpmnRef": f"60-apps/etzhayyim-project-states/data/gov/{iso3}/bpmn/{bpmn_name}" if has_bpmn else None,
        })
    # Build inline documents (top 4 contracts)
    inline_documents = []
    for c in contracts[:4]:
        cslug = c.get("contractSlug") or slug(c.get("name", ""))
        if not cslug: continue
        inline_documents.append({
            "id": f"{iso3}.{slug(cslug)}",
            "title": c.get("nameEn") or c.get("name", ""),
            "titleLocal": c.get("name", ""),
            "basis": c.get("legalBasis", ""),
            "uri": c.get("url", ""),
        })
    # stateProfile
    static = STATIC.get(iso3, {})
    profile_rec = {
        "$type": "com.etzhayyim.apps.states.stateProfile",
        "iso3": iso3, "name": name,
        "displayName": static.get("displayName") or f"Government of {name}",
        "description": f"{name} government registry - path-based DID, administrative desks, procedures (BPMN), and document templates.",
        "region": region, "status": "active",
        "addresses": static.get("addresses", []),
        "contacts": static.get("contacts", []),
        "desks": static.get("desks", []),
        "complianceFrameworks": static.get("complianceFrameworks", []),
        "procedures": static.get("procedures", []) + inline_procedures,
        "documentTemplates": static.get("documentTemplates", []) + inline_documents,
        "ministryCount": len(ministries),
        "contractCount": len(contracts),
        "bpmnCount": len(bpmn_files),
        "dataSourceRef": f"60-apps/etzhayyim-project-states/data/gov/{iso3}/",
        "createdAt": "2026-04-18T04:00:00Z",
    }
    (out_dir / "profile").mkdir(parents=True, exist_ok=True)
    (out_dir / "profile" / f"{iso3}.json").write_text(
        json.dumps(put_body("com.etzhayyim.apps.states.stateProfile", iso3, profile_rec), ensure_ascii=False))

    # stateProcedure (one per ministry with BPMN)
    (out_dir / "procedure").mkdir(parents=True, exist_ok=True)
    proc_count = 0
    for m in ministries[:20]:  # cap per-country to control volume
        path = m.get("path") or m.get("slug") or slug(m.get("name", ""))
        if not path: continue
        rkey = f"{iso3}-{slug(path)}"[:64]
        bpmn_name = path.replace(":", "-") + ".bpmn"
        has_bpmn = bpmn_name in bpmn_files
        proc_rec = {
            "$type": "com.etzhayyim.apps.states.stateProcedure",
            "iso3": iso3, "path": path,
            "title": m.get("nameEn") or m.get("name", ""),
            "titleLocal": m.get("name", ""),
            "authority": m.get("name", ""),
            "basis": m.get("contract", ""),
            "portalUri": m.get("website", ""),
            "orgTier": m.get("orgTier", "ministry"),
            "tags": m.get("tags", []),
            "bpmnRef": f"60-apps/etzhayyim-project-states/data/gov/{iso3}/bpmn/{bpmn_name}" if has_bpmn else None,
            "createdAt": "2026-04-18T03:30:00Z",
        }
        (out_dir / "procedure" / f"{rkey}.json").write_text(
            json.dumps(put_body("com.etzhayyim.apps.states.stateProcedure", rkey, proc_rec), ensure_ascii=False))
        proc_count += 1

    # stateDocument (one per contract/law)
    (out_dir / "document").mkdir(parents=True, exist_ok=True)
    doc_count = 0
    for c in contracts[:15]:  # cap
        cslug = c.get("contractSlug") or slug(c.get("name", ""))
        if not cslug: continue
        rkey = f"{iso3}-{slug(cslug)}"[:64]
        doc_rec = {
            "$type": "com.etzhayyim.apps.states.stateDocument",
            "iso3": iso3, "slug": cslug,
            "title": c.get("nameEn") or c.get("name", ""),
            "titleLocal": c.get("name", ""),
            "basis": c.get("legalBasis", ""),
            "effectiveDate": c.get("effectiveDate", ""),
            "uri": c.get("url", ""),
            "govLevel": c.get("govLevel", ""),
            "cofogCode": c.get("cofogCode", ""),
            "contractDid": c.get("contractDid", ""),
            "tags": c.get("tags", []),
            "createdAt": "2026-04-18T03:30:00Z",
        }
        (out_dir / "document" / f"{rkey}.json").write_text(
            json.dumps(put_body("com.etzhayyim.apps.states.stateDocument", rkey, doc_rec), ensure_ascii=False))
        doc_count += 1
    return (1, proc_count, doc_count)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", help="comma-separated iso3 list (default: all with data)")
    ap.add_argument("--out", default="/tmp/state-records", help="output dir")
    args = ap.parse_args()

    if args.iso:
        isos = [x.strip().lower() for x in args.iso.split(",") if x.strip()]
    else:
        # Union: countries with local data ndjson + countries with static-profile-data entries
        # (microstates without ndjson still get records from static data alone).
        with_data = {d.name for d in DATA_DIR.iterdir()
                     if d.is_dir() and (d / "contract.ndjson").exists() and (d / "contract.ndjson").stat().st_size > 0}
        from_static = set(STATIC.keys())
        isos = sorted(with_data | from_static)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    total_p = total_pr = total_d = 0
    for iso in isos:
        p, pr, d = emit_country(iso, out_dir)
        total_p += p; total_pr += pr; total_d += d
        print(f"  {iso}: profile={p} procedures={pr} documents={d}")
    print(f"\nTotal: {total_p} profiles, {total_pr} procedures, {total_d} documents")
    print(f"Output dir: {out_dir}")

if __name__ == "__main__":
    main()
