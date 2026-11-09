#!/usr/bin/env python3
"""Build data/market.json (read by /metrics) from the shared BP-Ontrac market pull.

Usage:
  python3 tools/build_market_json.py market_full.csv roster.json "Nov 9, 2026" data/market.json

market_full.csv  One row per market, fiscal month and tech, plus one row per market and month
                 with tech_id "_team" holding BP-Ontrac's Totals row. Columns: market, then the
                 scorecard's metrics.csv columns (period_start ... repeat_rate). Labels like
                 "Nov FM (to date)" are shown as "Nov FM".
roster.json      {"Dade": {"team": "Miami techs", "roster": [{"id","name","sup"}, ...]}, "Broward": {...}}
                 Working techs and supervisors, taken from the live Shift Calendar site.
                 Techs not on the roster are left out of the page.
"""
import csv, json, sys

COLS = ["jobs", "installs", "tcs", "tu_res", "tu_elig", "tu", "prom", "det", "surveys", "tnps",
        "ftr_fail", "ftr_jobs", "ftr", "pht", "appts", "met_appts", "met", "rework", "repeat"]
SRC = ["total_jobs", "installs", "tcs", "tu_result", "tu_eligible", "tool_usage", "promoters", "detractors",
       "tnps_surveys", "tnps_rate", "ftr_fail_jobs", "ftr_total_jobs", "ftr_pct", "pht_pass_pct",
       "total_appts", "met_appts", "met_rate", "rework_rate", "repeat_rate"]


def num(v):
    v = (v or "").strip().replace(",", "").replace("%", "")
    try:
        return float(v)
    except ValueError:
        return 0.0


def mdy(iso):
    y, m, d = iso.split("-")
    return f"{m}/{d}/{y}"


def main(csv_path, roster_path, pulled, out_path):
    rosters = json.load(open(roster_path, encoding="utf-8"))
    markets = {}
    for r in csv.DictReader(open(csv_path, encoding="utf-8-sig")):
        mk = r["market"].strip()
        if mk not in rosters:
            continue
        months = markets.setdefault(mk, {})
        key = r["period_start"]
        mo = months.setdefault(key, {"label": r["period_label"].replace(" (to date)", "").strip(),
                                     "start": mdy(r["period_start"]), "end": mdy(r["period_end"]),
                                     "team": None, "techs": {}})
        vals = [num(r[c]) for c in SRC]
        if r["tech_id"].strip() == "_team":
            mo["team"] = vals
        else:
            mo["techs"][r["tech_id"].strip()] = vals
    out = {"pulled": pulled, "cols": COLS,
           "note": "Shared BP-Ontrac Team Metrics by fiscal month. Read by the market-metrics page (index.html). Rebuilt by the refresh-scorecard skill.",
           "markets": {}}
    for mk, months in markets.items():
        ids = {t["id"] for t in rosters[mk]["roster"]}
        ml = [months[k] for k in sorted(months)]
        for mo in ml:
            mo["techs"] = {k: v for k, v in sorted(mo["techs"].items()) if k in ids}
            if mo["team"] is None:
                raise SystemExit(f"{mk} {mo['label']}: missing the _team (Totals) row")
        out["markets"][mk] = {"team": rosters[mk]["team"], "roster": rosters[mk]["roster"], "months": ml}
    json.dump(out, open(out_path, "w", encoding="utf-8"), separators=(",", ":"))
    for mk, m in out["markets"].items():
        print(mk, len(m["roster"]), "techs on roster,", ", ".join(f"{mo['label']} {len(mo['techs'])}" for mo in m["months"]))


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
