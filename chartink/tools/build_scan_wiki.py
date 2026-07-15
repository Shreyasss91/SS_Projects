#!/usr/bin/env python3
"""Build Chartink scan wiki from all_scans_raw.json exports.

Pipeline:
  1) Parse atlas_json into ordered filters with isEnabled + scan settings
  2) Write immutable source-snapshots (JSON + text)
  3) Generate one Markdown page per scan (template-compliant)
  4) Update docs/scan-wiki/README.md index
  5) Run source-fidelity QA and write QA report

Does not modify Chartink or invent missing UI state.
"""
from __future__ import annotations

import json
import hashlib
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
EXPORTS = ROOT / "data" / "exports"
WIKI = ROOT / "docs" / "scan-wiki"
SCANS_DIR = WIKI / "scans"
SNAP_DIR = WIKI / "source-snapshots"
QA_PATH = WIKI / "QA_REPORT.md"
SOURCE_AUDIT_PATH = WIKI / "SOURCE_AUDIT.md"
RAW_PATH = EXPORTS / "all_scans_raw.json"
PAGES_PATH = EXPORTS / "chartink_dashboard_pages.json"

IST = timezone(timedelta(hours=5, minutes=30))
CAPTURED_AT = "2026-07-15T12:56:06+05:30"  # export mtime (local export batch)
DASHBOARD_TOTAL = 478

# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path: Path) -> str:
    """Return the digest of the exact captured export bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_custom_indicators() -> dict[int, dict]:
    out: dict[int, dict] = {}
    if not PAGES_PATH.exists():
        return out
    pages = load_json(PAGES_PATH)
    if not pages:
        return out
    for item in pages[0].get("props", {}).get("customIndicators") or []:
        if isinstance(item, dict) and "id" in item:
            out[int(item["id"])] = item
    return out


def load_watchlists() -> dict[str, str]:
    """Map segment tokens / ids to display names."""
    out: dict[str, str] = {}
    if not PAGES_PATH.exists():
        return out
    pages = load_json(PAGES_PATH)
    for item in pages[0].get("props", {}).get("watchlistJson") or []:
        if isinstance(item, dict) and "id" in item and "name" in item:
            out[str(item["id"])] = str(item["name"])
            out[str(item["name"]).lower()] = str(item["name"])
    # built-ins
    for name in ("cash", "futures", "options", "currency", "commodity"):
        out[name] = name
    return out


# ---------------------------------------------------------------------------
# Atlas measure / condition renderer
# ---------------------------------------------------------------------------

OP_WORDS = {
    "crossed_above": "crossed above",
    "crossed_below": "crossed below",
    "default": "",
}


def humanize_measure_name(value: str | None, custom: dict[int, dict]) -> str:
    if not value:
        return "?"
    v = str(value)
    m = re.match(r"custom_indicator_(\d+)$", v)
    if m:
        cid = int(m.group(1))
        if cid in custom:
            return custom[cid].get("name") or v
        return v
    # Chartink-style spaced names
    replacements = {
        "%_change": "% change",
        "avg_true_range": "avg true range",
        "upper_bb": "upper bollinger band",
        "lower_bb": "lower bollinger band",
        "macd_line": "macd line",
        "macd_signal": "macd signal",
        "macd_histogram": "macd histogram",
        "fast_stochastic_%k": "fast stochastic %k",
        "fast_stochastic_%d": "fast stochastic %d",
        "slow_stochastic_%k": "slow stochastic %k",
        "slow_stochastic_%d": "slow stochastic %d",
        "ichimoku_span_a": "ichimoku span a",
        "ichimoku_span_b": "ichimoku span b",
        "ichimoku_base": "ichimoku base line",
        "ichimoku_conversion": "ichimoku conversion line",
        "ichimoku_cloud_top": "ichimoku cloud top",
        "ichimoku_cloud_bottom": "ichimoku cloud bottom",
        "pivot_point": "pivot point",
        "pivot_point_s1": "pivot point s1",
        "pivot_point_s2": "pivot point s2",
        "pivot_point_s3": "pivot point s3",
        "pivot_point_r1": "pivot point r1",
        "pivot_point_r2": "pivot point r2",
        "pivot_point_r3": "pivot point r3",
        "adx_di_positive": "adx di positive",
        "adx_di_negative": "adx di negative",
        "buy_orders_quantity_ratio": "buy orders quantity ratio",
        "sell_orders_quantity_ratio": "sell orders quantity ratio",
        "buyer_initiated_trades_quantity_ratio": "buyer initiated trades quantity ratio",
        "buyer_initiated_trades_ratio": "buyer initiated trades ratio",
        "buy_orders_quantity": "buy orders quantity",
        "sell_orders_quantity": "sell orders quantity",
        "market_cap": "market cap",
        "countstreak": "count streak",
    }
    if v in replacements:
        return replacements[v]
    return v.replace("_", " ")


def format_offset_prefix(offset: dict | None) -> str:
    """Return Chartink-like timeframe/offset prefix for a measure."""
    if not isinstance(offset, dict):
        return ""
    val = str(offset.get("value") or "0_days_ago")
    intra = offset.get("intradayOffsetValue")
    try:
        intra_i = int(str(intra).replace("=", "")) if intra is not None else 0
    except ValueError:
        intra_i = 0

    prefix = ""
    if val == "0_days_ago":
        prefix = "daily"
    elif val.endswith("_days_ago"):
        n = val.replace("_days_ago", "")
        if n == "0":
            prefix = "daily"
        elif n == "1":
            prefix = "1 day ago"
        else:
            prefix = f"{n} days ago"
    elif val.endswith("_weeks_ago"):
        n = val.replace("_weeks_ago", "")
        if n == "0":
            prefix = "weekly"
        elif n == "1":
            prefix = "1 week ago"
        else:
            prefix = f"{n} weeks ago"
    elif val.endswith("_months_ago"):
        n = val.replace("_months_ago", "")
        if n == "0":
            prefix = "monthly"
        elif n == "1":
            prefix = "1 month ago"
        else:
            prefix = f"{n} months ago"
    elif val.endswith("_minute"):
        n = val.replace("_minute", "")
        prefix = f"{n} minute"
    elif val.endswith("_hour"):
        n = val.replace("_hour", "")
        prefix = f"{n} hour"
    else:
        prefix = val.replace("_", " ")

    # bar offset annotation as in atlas_query: [0], [-1]
    if prefix.endswith("minute") or prefix.endswith("hour"):
        return f"[{intra_i}] {prefix}"
    if intra_i != 0 and prefix in ("daily", "weekly", "monthly"):
        # rare: bar shift on higher TF via intradayOffsetValue
        return f"[{intra_i}] {prefix}"
    return prefix


def render_number_param(param: dict, custom: dict[int, dict]) -> str:
    """Render a parameter node to text."""
    if not isinstance(param, dict):
        return str(param)
    ptype = param.get("type")
    if ptype == "input-number" or "inputValue" in param:
        iv = param.get("inputValue")
        if iv is not None and str(iv) != "":
            # nested field may still exist under dummy number
            field = param.get("field")
            if isinstance(field, dict) and field.get("type") == 5:
                # plain number constant
                return str(iv)
            return str(iv)
        field = param.get("field")
        if isinstance(field, dict):
            return render_expr_node(field, custom)
        return "0"
    if ptype in ("field", "enum", "boolean") or param.get("field") is not None:
        field = param.get("field")
        if isinstance(field, dict):
            return render_expr_node(field, custom)
        return ""
    if ptype is None and param.get("field") is not None:
        return render_expr_node(param["field"], custom)
    return str(param.get("inputValue") or param.get("value") or "")


def render_measure(measure: dict, custom: dict[int, dict]) -> str:
    if not isinstance(measure, dict):
        return "?"
    value = measure.get("value")
    offset = measure.get("offset") if isinstance(measure.get("offset"), dict) else {}
    params = measure.get("parameters") or []
    prefix = format_offset_prefix(offset)

    if value == "number":
        if params:
            return render_number_param(params[0], custom)
        # bare number may use inputValue on measure
        if measure.get("inputValue") not in (None, ""):
            return str(measure.get("inputValue"))
        return "0"

    if value == "brackets":
        # parameters hold inner field expression
        inner_parts = []
        for p in params:
            inner_parts.append(render_number_param(p, custom))
        inner = " ".join(x for x in inner_parts if x)
        return f"( {inner} )"

    name = humanize_measure_name(str(value), custom)

    # count / countstreak: Chartink uses whenField + inputValue lookback
    # (firstParameter is often the type label "number", not the numeric window)
    if value in ("count", "countstreak"):
        lookback = measure.get("inputValue")
        fp = measure.get("firstParameter")
        if lookback in (None, "") and fp is not None and str(fp) not in ("number", "field", "enum", "boolean"):
            lookback = fp
        when = measure.get("whenField")
        when_txt = render_expr_node(when, custom) if isinstance(when, dict) else ""
        if lookback not in (None, "") and when_txt:
            body = f"{name}( {lookback}, 1 where {when_txt} )"
        elif when_txt:
            body = f"{name}( where {when_txt} )"
        elif lookback not in (None, ""):
            body = f"{name}( {lookback} )"
        else:
            body = name
        if prefix:
            return f"{prefix} {body}"
        return body
    # Collect parameter strings (periods etc.)
    arg_parts: list[str] = []
    for p in params:
        arg_parts.append(render_number_param(p, custom))
    # Filter empty
    arg_parts = [a for a in arg_parts if a is not None and str(a) != ""]

    # Some measures take no args
    if not arg_parts:
        body = name
    else:
        # Chartink style: rsi( 14 ), sma(close, 20), max( 10 , daily high )
        joined = " ,  ".join(arg_parts)
        body = f"{name}( {joined} )"

    if prefix:
        return f"{prefix} {body}"
    return body

def render_expr_node(node: dict, custom: dict[int, dict]) -> str:
    """Render a type-2 (or type-5 leaf) expression node to Chartink-like text."""
    if not isinstance(node, dict):
        return str(node)

    # type 5 often wraps measure with operation default
    measure = node.get("measure")
    operation = node.get("operation") if isinstance(node.get("operation"), dict) else {}
    op = operation.get("value") if operation else "default"
    field = operation.get("field") if operation else None

    left = render_measure(measure, custom) if isinstance(measure, dict) else ""

    if not op or op == "default" or field is None:
        return left

    op_txt = OP_WORDS.get(str(op), str(op))
    right = render_expr_node(field, custom) if isinstance(field, dict) else ""

    if op in ("crossed_above", "crossed_below"):
        return f"{left} {op_txt} {right}".strip()
    if op in (">", "<", ">=", "<=", "=", "!=", "+", "-", "*", "/"):
        return f"{left} {op} {right}".strip()
    return f"{left} {op_txt} {right}".strip()


def segment_display(segment: str | None, watchlists: dict[str, str]) -> str:
    if not segment:
        return "unspecified"
    s = str(segment)
    # patterns: "nifty 200_46553", "cash", "futures_33489", "SBIN_359443"
    if "_" in s:
        name_part, id_part = s.rsplit("_", 1)
        if id_part.isdigit() or (id_part.startswith("-") and id_part[1:].isdigit()):
            if id_part in watchlists:
                return watchlists[id_part]
            return name_part
    if s.lower() in watchlists:
        return watchlists[s.lower()]
    if s in watchlists:
        return watchlists[s]
    return s


# ---------------------------------------------------------------------------
# Tree walk: extract ordered filters + settings
# ---------------------------------------------------------------------------


def extract_filters(
    group: dict,
    custom: dict[int, dict],
    watchlists: dict[str, str],
    path: str = "root",
    ordinal_start: int = 1,
) -> tuple[list[dict], int]:
    """Return (filters, next_ordinal). Each filter is a condition or subgroup summary."""
    filters: list[dict] = []
    n = ordinal_start
    if not isinstance(group, dict):
        return filters, n

    children = group.get("children") or []
    for child in children:
        if not isinstance(child, dict):
            continue
        ctype = child.get("type")
        if ctype == 3:
            # nested group
            seg = segment_display(child.get("segment"), watchlists)
            join = child.get("join") or "all"
            en = bool(child.get("isEnabled", True))
            # expand nested conditions as individual filters with group path
            nested_path = f"{path}/group[{seg}|{join}]"
            # group header row
            filters.append(
                {
                    "ordinal": n,
                    "kind": "group",
                    "status": "Enabled" if en else "Disabled",
                    "is_enabled": en,
                    "group_path": nested_path,
                    "segment": seg,
                    "join": join,
                    "combination": child.get("combination"),
                    "measurevalue": child.get("measurevalue"),
                    "verbatim": (
                        f"[GROUP segment={seg} join={join} combination={child.get('combination')} "
                        f"measurevalue={child.get('measurevalue')}]"
                    ),
                    "raw": child,
                }
            )
            n += 1
            nested, n = extract_filters(child, custom, watchlists, nested_path, n)
            filters.extend(nested)
        elif ctype == 2:
            en = bool(child.get("isEnabled", True))
            text = render_expr_node(child, custom)
            filters.append(
                {
                    "ordinal": n,
                    "kind": "condition",
                    "status": "Enabled" if en else "Disabled",
                    "is_enabled": en,
                    "group_path": path,
                    "verbatim": text,
                    "raw": child,
                }
            )
            n += 1
        else:
            # unknown node — still record
            filters.append(
                {
                    "ordinal": n,
                    "kind": f"type_{ctype}",
                    "status": "Needs review",
                    "is_enabled": child.get("isEnabled"),
                    "group_path": path,
                    "verbatim": json.dumps(child, default=str)[:500],
                    "raw": child,
                }
            )
            n += 1
    return filters, n


def collect_timeframes(node: Any, bag: set[str]) -> None:
    if isinstance(node, dict):
        if isinstance(node.get("offset"), dict):
            bag.add(str(node["offset"].get("value") or ""))
        for v in node.values():
            collect_timeframes(v, bag)
    elif isinstance(node, list):
        for x in node:
            collect_timeframes(x, bag)


def collect_measures(node: Any, bag: Counter) -> None:
    if isinstance(node, dict):
        if "measure" in node and isinstance(node["measure"], dict):
            val = node["measure"].get("value")
            if val and val not in ("number", "brackets"):
                bag[str(val)] += 1
        for v in node.values():
            collect_measures(v, bag)
    elif isinstance(node, list):
        for x in node:
            collect_measures(x, bag)


def collect_ops(node: Any, bag: Counter) -> None:
    if isinstance(node, dict):
        if node.get("type") == 2 and isinstance(node.get("operation"), dict):
            op = node["operation"].get("value")
            if op and op != "default":
                bag[str(op)] += 1
        for v in node.values():
            collect_ops(v, bag)
    elif isinstance(node, list):
        for x in node:
            collect_ops(x, bag)


def parse_scan(raw: dict, custom: dict[int, dict], watchlists: dict[str, str]) -> dict:
    aj = raw.get("atlas_json")
    if isinstance(aj, str):
        aj = json.loads(aj)
    group = aj.get("group") if isinstance(aj, dict) else {}
    filters, _ = extract_filters(group or {}, custom, watchlists)

    conditions = [f for f in filters if f["kind"] == "condition"]
    enabled = [f for f in conditions if f["status"] == "Enabled"]
    disabled = [f for f in conditions if f["status"] == "Disabled"]
    needs = [f for f in conditions if f["status"] == "Needs review"]

    tfs: set[str] = set()
    collect_timeframes(aj, tfs)
    measures: Counter = Counter()
    collect_measures(aj, measures)
    ops: Counter = Counter()
    collect_ops(aj, ops)
    enabled_measures: Counter = Counter()
    enabled_ops: Counter = Counter()
    for f in enabled:
        collect_measures(f["raw"], enabled_measures)
        collect_ops(f["raw"], enabled_ops)

    root_seg = segment_display(group.get("segment") if group else None, watchlists)
    root_join = (group or {}).get("join") or "all"
    root_combo = (group or {}).get("combination")
    root_mv = (group or {}).get("measurevalue")

    slug = raw.get("slug") or str(raw.get("id"))
    url = f"https://chartink.com/screener/{slug}"
    name = (raw.get("name") or f"Scan {raw.get('id')}").strip()

    # Build verbatim definition text including disabled filters
    lines = [
        f"Scan name: {name}",
        f"Scan id: {raw.get('id')}",
        f"Slug: {slug}",
        f"Source URL: {url}",
        f"Root universe/segment: {root_seg}",
        f"Root join: {root_join} ({'AND' if root_join == 'all' else 'OR' if root_join == 'any' else root_join})",
        f"Root combination: {root_combo}",
        f"Root measurevalue: {root_mv}",
        f"is_private: {raw.get('is_private')}",
        f"created_at: {raw.get('created_at')}",
        "",
        "=== Source-faithful rendered tree from atlas_json (includes Enabled and Disabled) ===",
        "",
    ]
    for f in filters:
        if f["kind"] == "group":
            lines.append(
                f"{f['ordinal']}. [{f['status']}] {f['verbatim']}  (path: {f['group_path']})"
            )
        else:
            lines.append(
                f"{f['ordinal']}. [{f['status']}] {f['verbatim']}"
            )
            if f.get("group_path") and f["group_path"] != "root":
                lines.append(f"    group_path: {f['group_path']}")

    lines += [
        "",
        "=== Literal Chartink atlas_query (compiled active query; typically omits disabled filters) ===",
        "",
        str(raw.get("atlas_query") or "").strip() or "(empty)",
    ]

    return {
        "scan_id": raw.get("id"),
        "scan_name": name,
        "slug": slug,
        "source_url": url,
        "description": raw.get("description"),
        "created_at": raw.get("created_at"),
        "is_private": raw.get("is_private"),
        "is_favourite": raw.get("is_favourite"),
        "is_alert_present": raw.get("is_alert_present"),
        "atlas_query": raw.get("atlas_query"),
        "atlas_json": aj,
        "filters": filters,
        "conditions": conditions,
        "enabled_filters": enabled,
        "disabled_filters": disabled,
        "needs_review_filters": needs,
        "enabled_filter_count": len(enabled),
        "disabled_filter_count": len(disabled),
        "needs_review_count": len(needs),
        "root_segment": root_seg,
        "root_join": root_join,
        "root_combination": root_combo,
        "root_measurevalue": root_mv,
        "timeframes_raw": sorted(t for t in tfs if t),
        "measures": measures,
        "ops": ops,
        "enabled_measures": enabled_measures,
        "enabled_ops": enabled_ops,
        "verbatim_definition": "\n".join(lines),
        "captured_at": CAPTURED_AT,
    }


# ---------------------------------------------------------------------------
# Classification + analysis
# ---------------------------------------------------------------------------

INTRADAY_TF = re.compile(r"(_minute|_hour|\bminute\b|\bhour\b|1_minute|5_minute|15_minute|30_minute|60_minute|75_minute|120_minute|240_minute)")
WEEKLY_TF = re.compile(r"weeks_ago|weekly")
MONTHLY_TF = re.compile(r"months_ago|monthly")


def classify_horizon(parsed: dict) -> str:
    """Classify horizon from expression timeframes, not scan titles."""
    tfs = " ".join(parsed["timeframes_raw"])
    has_intraday = bool(INTRADAY_TF.search(tfs))
    has_weekly = bool(WEEKLY_TF.search(tfs))
    has_monthly = bool(MONTHLY_TF.search(tfs))
    has_daily = "days_ago" in tfs
    if sum((has_intraday, has_weekly, has_monthly)) > 1:
        return "Multi-horizon"
    if has_intraday:
        return "Intraday"
    if has_monthly:
        return "Positional"
    if has_weekly or has_daily:
        return "Swing"
    return "Unspecified"


def classify_methods(parsed: dict) -> list[str]:
    """Classify only from enabled leaves; title words never supply a method tag."""
    measures = set(parsed["enabled_measures"].keys())
    ops = set(parsed["enabled_ops"].keys())
    active = " ".join(f["verbatim"].lower() for f in parsed["enabled_filters"])
    scored: dict[str, int] = {}

    def add(method: str, weight: int) -> None:
        scored[method] = scored.get(method, 0) + weight

    ma = {"sma", "ema", "wma", "hma", "vwma", "ichimoku_span_a", "ichimoku_span_b", "ichimoku_base", "ichimoku_conversion", "ichimoku_cloud_top", "ichimoku_cloud_bottom"}
    oscillator = {"rsi", "macd_line", "macd_signal", "macd_histogram", "cci", "mfi", "fast_stochastic_%k", "fast_stochastic_%d", "slow_stochastic_%k", "slow_stochastic_%d", "aroon_up", "aroon_down", "adx_di_positive", "adx_di_negative", "cmo", "roc", "ppo"}
    volume = {"volume", "obv", "accdist", "vwap", "buy_orders_quantity", "buy_orders_quantity_ratio", "sell_orders_quantity", "sell_orders_quantity_ratio", "buyer_initiated_trades_ratio", "buyer_initiated_trades_quantity_ratio", "traded_value", "delivery_percentage"}
    volatility = {"upper_bb", "lower_bb", "avg_true_range", "stddva", "standard_deviation"}
    pivots = {"pivot_point", "pivot_point_s1", "pivot_point_s2", "pivot_point_s3", "pivot_point_r1", "pivot_point_r2", "pivot_point_r3"}
    fundamentals = {"market_cap", "pe", "pb", "eps", "roe", "roce", "sales", "net_profit", "debt_to_equity"}

    if measures & ma:
        add("Moving average", 5)
        if "ichimoku" in active or "crossed_above" in ops or "crossed_below" in ops:
            add("Trend following", 2)
    if measures & oscillator:
        add("Oscillator", 5)
        if "crossed_above" in ops or "crossed_below" in ops or any(x in measures for x in ("roc", "ppo", "cmo")):
            add("Momentum", 2)
        if any(token in active for token in (" rsi( 14 ) < 30", " rsi( 14 ) > 70", "oversold", "overbought")):
            add("Mean reversion", 2)
    if measures & volume:
        add("Volume/delivery", 5)
    if measures & volatility:
        add("Volatility", 5)
    if measures & pivots:
        add("Support/resistance", 5)
    if measures & fundamentals:
        add("Fundamental", 5)
    if any(x in measures for x in ("open", "high", "low", "close", "heikin_ashi_open", "heikin_ashi_close")):
        add("Price action", 1)
    if "max" in measures and "high" in measures and ("crossed_above" in ops or "close >" in active or "high >" in active):
        add("Breakout", 4)
    if "min" in measures and "low" in measures and ("crossed_below" in ops or "close <" in active or "low <" in active):
        add("Breakout", 3)
    if "max" in measures and "min" in measures and "high" in measures and "low" in measures:
        add("Volatility", 2)
    if "crossed_above" in ops or "crossed_below" in ops:
        add("Momentum", 1)

    if len(scored) > 1 and scored.get("Price action") == 1:
        del scored["Price action"]
    if not scored:
        return ["Other"]
    methods = [method for method, _ in sorted(scored.items(), key=lambda item: (-item[1], item[0]))]
    if len(methods) >= 3:
        methods.append("Multi-factor")
    return methods


def classify_tags(parsed: dict) -> list[str]:
    """Apply context tags from enabled conditions and captured segment only."""
    tags: list[str] = []
    measures = set(parsed["enabled_measures"].keys())
    active = " ".join(f["verbatim"].lower() for f in parsed["enabled_filters"])
    seg = (parsed.get("root_segment") or "").lower()

    if "crossed above" in active or " > " in active:
        tags.append("bias:upward-condition")
    if "crossed below" in active or " < " in active:
        tags.append("bias:downward-condition")

    universe_tags = (("nifty 50", "universe:nifty-50"), ("nifty 100", "universe:nifty-100"), ("nifty 200", "universe:nifty-200"), ("nifty 500", "universe:nifty-500"), ("midcap", "universe:midcap"), ("future", "universe:futures"), ("index", "universe:index"))
    matched_universe = next((tag for key, tag in universe_tags if key in seg), None)
    tags.append(matched_universe or ("universe:cash" if seg == "cash" else f"universe:{seg.replace(' ', '-')[:40]}"))

    fam_map = (("rsi", "rsi"), ("macd", "macd"), ("ichimoku", "ichimoku"), ("vwap", "vwap"), ("upper_bb", "bollinger"), ("lower_bb", "bollinger"), ("stochastic", "stochastic"), ("adx", "adx"), ("avg_true_range", "atr"), ("mfi", "mfi"), ("cci", "cci"), ("volume", "volume"), ("pivot", "pivot"), ("ema", "ema"), ("sma", "sma"), ("aroon", "aroon"), ("obv", "obv"))
    measure_blob = " ".join(measures)
    for key, tag in fam_map:
        if key in measure_blob:
            tags.append(f"indicator:{tag}")

    for tf in parsed["timeframes_raw"]:
        if "minute" in tf or "hour" in tf:
            tags.append("timeframe:intraday-bars")
        elif "weeks" in tf:
            tags.append("timeframe:weekly")
        elif "months" in tf:
            tags.append("timeframe:monthly")
        elif "days" in tf:
            tags.append("timeframe:daily")
    return list(dict.fromkeys(tags))


def explain_filter(verbatim: str, status: str) -> str:
    """Short calculation meaning for one filter row."""
    v = verbatim.lower()
    parts: list[str] = []

    if "crossed above" in v:
        parts.append("Requires a bullish crossover event (left series moves from at/below to above the right series on the selected bar).")
    elif "crossed below" in v:
        parts.append("Requires a bearish crossover event (left series moves from at/above to below the right series on the selected bar).")
    elif " > " in v or v.strip().endswith(">"):
        parts.append("Inequality test: left expression must be strictly greater than right.")
    elif " < " in v:
        parts.append("Inequality test: left expression must be strictly less than right.")
    elif " >= " in v:
        parts.append("Inequality test: left expression must be greater than or equal to right.")
    elif " <= " in v:
        parts.append("Inequality test: left expression must be less than or equal to right.")
    elif " = " in v:
        parts.append("Equality test between left and right expressions.")
    elif " != " in v:
        parts.append("Inequality (not-equal) test between left and right expressions.")
    elif " - " in v and (" > " in v or " < " in v or "*" in v):
        parts.append("Arithmetic comparison involving a difference of price/indicator series.")
    else:
        parts.append("Boolean condition on Chartink measure expressions as written.")

    # indicator hints
    hints = []
    if "rsi" in v:
        hints.append("RSI is a momentum oscillator from average gains/losses over its period.")
    if "macd" in v:
        hints.append("MACD uses EMA differences (line/signal/histogram depending on field).")
    if "ichimoku" in v:
        hints.append("Ichimoku components (conversion/base/spans) describe equilibrium and cloud structure.")
    if "sma(" in v or " sma" in v:
        hints.append("SMA is the arithmetic mean of the chosen field over N bars.")
    if "ema(" in v or " ema" in v:
        hints.append("EMA is an exponentially weighted moving average of the chosen field.")
    if "vwap" in v:
        hints.append("VWAP is volume-weighted average price for the session/period context Chartink supplies.")
    if "volume" in v:
        hints.append("Volume condition gates participation/liquidity.")
    if "bollinger" in v or "upper bollinger" in v or "lower bollinger" in v:
        hints.append("Bollinger fields are typically a moving average ± standard-deviation bands.")
    if "atr" in v or "avg true range" in v:
        hints.append("ATR measures smoothed true range (volatility), not direction.")
    if "stochastic" in v:
        hints.append("Stochastic compares close location within a high-low range over its lookback.")
    if "pivot" in v:
        hints.append("Pivot fields are classic floor-trader support/resistance levels from prior period H/L/C.")
    if "max(" in v:
        hints.append("max(N, series) is the highest value of series over N bars.")
    if "min(" in v:
        hints.append("min(N, series) is the lowest value of series over N bars.")
    if "market cap" in v:
        hints.append("Filters by market-capitalisation field from Chartink fundamentals.")
    if "minute" in v:
        hints.append("Uses an intraday bar size (minute timeframe) rather than daily-only data.")
    if "weekly" in v or "week ago" in v:
        hints.append("References weekly bars / weekly offset.")
    if "monthly" in v or "month ago" in v:
        hints.append("References monthly bars / monthly offset.")

    if status == "Disabled":
        parts.append("Currently disabled in source — not applied when the scan runs.")
    if hints:
        parts.append(" ".join(hints[:3]))
    return " ".join(parts)


def write_purpose(parsed: dict, methods: list[str], horizon: str) -> str:
    """State the enabled tests up front instead of inferring purpose from the title."""
    seg = parsed["root_segment"]
    enabled = parsed["enabled_filters"]
    join = parsed["root_join"]
    join_word = "all (AND)" if join == "all" else "any (OR)" if join == "any" else join
    lines = [
        f"This is a **{horizon.lower()}** screen over **{seg}** with **{len(enabled)}** active leaf condition(s) under root join **{join_word}**.",
        f"Its method labels are derived only from active expressions: **{', '.join(methods)}**.",
    ]
    if enabled:
        lines.append("The active tests, in captured order, are:")
        for f in enabled:
            lines.append("- " + f["verbatim"])
    else:
        lines.append("No enabled leaf conditions were recovered; this page needs source review.")
    if parsed.get("description"):
        lines.append(f"\nAuthor description (source metadata): {parsed['description'].strip()}")
    lines.append("\nThis explains the captured screen mechanically; it is not a performance claim or trade recommendation.")
    return "\n".join(lines)


def write_enabled_logic(parsed: dict) -> str:
    enabled = parsed["enabled_filters"]
    join = parsed["root_join"]
    join_word = "AND (all must pass)" if join == "all" else "OR (any may pass)" if join == "any" else join
    lines = [
        f"Root group join is **{join_word}**. Nested groups may introduce additional AND/OR scopes "
        f"(see the rendered source tree and the group-scope column in the filter table).",
        f"There are **{len(enabled)}** enabled leaf conditions. Disabled conditions are ignored at runtime.",
        "",
    ]
    if not enabled:
        lines.append(
            "No enabled leaf conditions were found in atlas_json. Treat this scan as **Needs review** — "
            "it may rely on group structure only, be incomplete, or require UI verification."
        )
        return "\n".join(lines)

    lines.append("Role of each enabled condition:")
    for f in enabled:
        lines.append(f"- **#{f['ordinal']}** `{f['verbatim']}` — {explain_filter(f['verbatim'], 'Enabled')}")

    lines += [
        "",
        "Combined effect:",
        f"- With root join **{join}**, the scan is "
        + (
            "more selective (intersection of conditions)."
            if join == "all"
            else "broader (union of conditions)."
            if join == "any"
            else "governed by the stated join operator."
        ),
        "- Nested groups with their own segment fields re-scope symbols (e.g. a cash sub-group inside an index universe).",
        "- Crossover operators (`crossed above` / `crossed below`) act as **event triggers**; level comparisons act as **regime or location filters**.",
        "- Volume, market-cap, and order-flow fields (when present) usually act as **participation/liquidity gates** rather than directional triggers.",
    ]
    return "\n".join(lines)


def write_disabled_section(parsed: dict) -> str:
    disabled = parsed["disabled_filters"]
    if not disabled:
        return (
            "No disabled leaf conditions were present in the captured `atlas_json` tree. "
            "Nothing additional is withheld solely by UI disable toggles at the condition level."
        )
    lines = [
        f"There are **{len(disabled)}** disabled leaf condition(s). "
        "Reasons for disabling are **not stated in source metadata** unless the description says so; "
        "the notes below are inference about what enabling each would do.",
        "",
    ]
    for f in disabled:
        lines.append(f"### Disabled #{f['ordinal']}")
        lines.append(f"- **Condition (verbatim):** `{f['verbatim']}`")
        lines.append(f"- **Meaning:** {explain_filter(f['verbatim'], 'Disabled')}")
        lines.append(
            "- **If enabled:** would add this constraint to the active boolean tree (subject to its group join), "
            "likely changing candidate count and timing."
        )
        lines.append(
            "- **Trade-offs:** enabling usually increases selectivity and may remove early or noisy matches; "
            "keeping it disabled preserves a wider (or differently timed) set of results."
        )
        lines.append("")
    return "\n".join(lines)


def write_calculation_notes(parsed: dict) -> str:
    measures = parsed["measures"]
    ops = parsed["ops"]
    lines = [
        "Notes below are tied to measures actually present in this scan's tree. "
        "Chartink-specific aggregation/session rules are used as Chartink implements them; "
        "where the export does not document a quirk, uncertainty is left explicit.",
        "",
        "### Measures observed",
    ]
    if not measures:
        lines.append("- (no named measures extracted)")
    else:
        for m, c in measures.most_common(25):
            lines.append(f"- `{humanize_measure_name(m, {})}` — appears {c} time(s) in the expression tree")

    lines.append("")
    lines.append("### Operators observed")
    if not ops:
        lines.append("- (no comparison/arithmetic operators beyond defaults)")
    else:
        for o, c in ops.most_common(20):
            lines.append(f"- `{OP_WORDS.get(o, o)}` — {c} occurrence(s)")

    lines += [
        "",
        "### General calculation semantics used in this corpus",
        "- **Offsets** such as `0_days_ago` / `1_days_ago` / `N_minute` select bar size and historical shift.",
        "- **Intraday bar index** in `[k] N minute ...` denotes the k-th bar offset on that minute timeframe in Chartink's query language.",
        "- **max(N, series) / min(N, series)** are rolling extrema.",
        "- **sma / ema / wma / hma / vwma** are moving averages of the nested field over the given length.",
        "- **RSI / MFI / CCI / Stochastic / MACD / ADX DI / Aroon** are standard technical indicators with periods from parameters.",
        "- **Ichimoku** spans/base/conversion use the classic 9/26/52 parameterisation when those numbers appear.",
        "- **Custom indicators** resolve via the dashboard `customIndicators` list when the export includes them; otherwise the raw `custom_indicator_<id>` token is retained.",
        "",
        f"### Scan-level settings (from root group)",
        f"- Universe/segment: **{parsed['root_segment']}**",
        f"- Join: **{parsed['root_join']}**",
        f"- Combination: **{parsed['root_combination']}**",
        f"- Measurevalue: **{parsed['root_measurevalue']}**",
        f"- Timeframe tokens: {', '.join(f'`{t}`' for t in parsed['timeframes_raw']) or 'none extracted'}",
    ]
    # custom indicator expansions
    return "\n".join(lines)


def write_how_to_use(parsed: dict, horizon: str, methods: list[str]) -> str:
    return "\n".join(
        [
            f"- **Horizon context:** treat as **{horizon}** unless live bar size usage suggests otherwise; confirm against the timeframe tokens in the definition.",
            f"- **Universe:** results are scoped to **{parsed['root_segment']}**. Liquidity and index membership still vary inside that set.",
            f"- **Method context:** {', '.join(methods)}.",
            "- **Workflow (educational):** run near the bar close of the controlling timeframe so incomplete bars do not flip crossovers; compare hits to price structure, news, and broader market breadth before any decision.",
            "- **Confirmation ideas (not required by the scan):** higher-timeframe trend agreement, volume quality, distance from obvious resistance/support, and avoiding illiquid names even if they pass numeric filters.",
            "- **Invalidation framing (educational):** a failed hold of the trigger level, opposing crossover, or loss of the regime filter (e.g. falling back through a moving average / cloud) often re-characterises the setup; the scan itself does not define stops.",
            "- **Operational constraints:** Chartink data latency, corporate actions, session holidays, and futures vs cash differences can change membership. Intraday scans are especially sensitive to the exact minute bar and whether the last bar is complete.",
            "- **Risk:** screening is not execution. Position sizing, brokerage, slippage, and gaps are outside this definition.",
        ]
    )


def write_strengths(parsed: dict, methods: list[str]) -> str:
    points = [
        f"- Explicit, machine-readable condition tree with **{parsed['enabled_filter_count']}** active filters — transparent screening logic.",
        f"- Universe pinned to **{parsed['root_segment']}**, which reduces accidental all-market noise relative to an unbounded cash list (when the segment is an index).",
    ]
    if "Breakout" in methods:
        points.append("- Breakout-oriented comparisons can surface range expansion candidates early when volume/regime filters confirm.")
    if "Oscillator" in methods:
        points.append("- Oscillator thresholds/crossovers give objective momentum or stretch readouts that are easy to audit.")
    if "Volume/delivery" in methods:
        points.append("- Participation filters help de-emphasise thin prints that only move on tiny size.")
    if "Moving average" in methods or "Trend following" in methods:
        points.append("- Moving-average / Ichimoku structure provides a simple regime filter that is easy to chart-check.")
    if "Mean reversion" in methods:
        points.append("- Stretch conditions can highlight exhaustion zones inside ranges when broader trend is not strongly opposed.")
    if parsed["disabled_filter_count"]:
        points.append(
            f"- Retains **{parsed['disabled_filter_count']}** disabled filter(s) in source — useful experimental toggles without losing history of the idea."
        )
    if parsed["root_join"] == "all":
        points.append("- AND-combined root group increases selectivity versus single-condition scans.")
    if parsed["root_join"] == "any":
        points.append("- OR-combined root group can cast a wider net across related patterns.")
    return "\n".join(points)


def write_limitations(parsed: dict, methods: list[str]) -> str:
    points = [
        "- **No predictive guarantee:** passing filters only means the boolean tree is true on Chartink's data at evaluation time.",
        "- **Lookahead / incomplete bar risk:** crossovers on forming candles can appear and disappear before close.",
        "- **Parameter sensitivity:** fixed periods and thresholds can overfit recent regimes and fail when volatility shifts.",
    ]
    if "Breakout" in methods:
        points.append("- Breakout logic is prone to **false breaks** around news, low-liquidity opens, and range-bound chop.")
    if "Mean reversion" in methods:
        points.append("- Mean-reversion style thresholds can **fight strong trends** and produce repeated losers in momentum markets.")
    if "Oscillator" in methods:
        points.append("- Oscillators can stay overbought/oversold for long stretches; level tests are not automatic reversals.")
    if "Volume/delivery" in methods:
        points.append("- Volume spikes may reflect **block deals, F&O expiry, or one-off events** rather than sustainable interest.")
    if "Fundamental" in methods:
        points.append("- Fundamental fields can be **stale or vendor-specific**; always verify corporate data dates.")
    if any("minute" in t for t in parsed["timeframes_raw"]):
        points.append("- Intraday minute conditions increase **noise and session-boundary artifacts** (open auction, lunch liquidity).")
    if parsed["disabled_filter_count"]:
        points.append(
            "- Disabled filters mean the live behaviour is **looser or differently timed** than a reader might assume from a full written checklist."
        )
    if parsed["root_join"] == "any":
        points.append("- OR logic can admit symbols that only match a weak branch of the idea.")
    points.append(
        "- **Universe concentration:** index-limited scans miss setups outside the segment; cash-wide scans increase illiquid hits."
    )
    return "\n".join(points)


def write_classification_section(parsed: dict, horizon: str, methods: list[str], tags: list[str]) -> str:
    return "\n".join(
        [
            f"- **Horizon:** {horizon}",
            f"- **Methods:** {', '.join(methods)}",
            f"- **Tags:** {', '.join(tags)}",
            f"- **Root universe:** {parsed['root_segment']}",
            f"- **Root join:** {parsed['root_join']}",
            "- Related concepts are conceptual only; similar titles in the corpus are **not** merged or treated as duplicates without separate condition comparison.",
        ]
    )


# ---------------------------------------------------------------------------
# File naming / markdown emission
# ---------------------------------------------------------------------------


def safe_title(name: str, max_len: int = 60) -> str:
    s = re.sub(r"[^\w\s\-]+", "", name, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s.strip())
    s = s.strip("-_") or "scan"
    return s[:max_len].strip("-_").lower()


def page_filename(scan_id: Any, name: str) -> str:
    return f"{scan_id}--{safe_title(name)}.md"


def yaml_escape(s: str) -> str:
    if s is None:
        return '""'
    s = str(s).replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()
    # Always JSON-quote when special YAML / front-matter risk chars appear
    # (including '---' which confuses naive FM splitters).
    if (
        any(c in s for c in (":", "#", "{", "}", "[", "]", ",", "&", "*", "!", "|", ">", "'", '"', "%", "@", "`", "\\"))
        or "---" in s
        or s == ""
        or s.lower() in ("true", "false", "null")
        or s[:1].isdigit()
    ):
        return json.dumps(s, ensure_ascii=False)
    return s

def md_cell(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


def render_page(parsed: dict, custom: dict[int, dict]) -> str:
    horizon = classify_horizon(parsed)
    methods = classify_methods(parsed)
    tags = classify_tags(parsed)
    primary = methods[0] if methods else "Other"

    # rebuild calculation notes with custom names
    # (write_calculation_notes uses humanize without custom; patch measure list)
    calc = write_calculation_notes(parsed)
    # improve custom indicator lines
    for m in list(parsed["measures"].keys()):
        pretty = humanize_measure_name(m, custom)
        if pretty != m.replace("_", " ") and m.startswith("custom_indicator_"):
            calc = calc.replace(f"`{m.replace('_', ' ')}`", f"`{pretty}` ({m})")

    # The interpretation table is deliberately leaf-only. Group structure remains intact
    # in the source-faithful tree and appears here only as scope.
    filter_rows = []
    for leaf_number, f in enumerate(parsed["conditions"], 1):
        scope = f.get("group_path") or "root"
        filter_rows.append(
            f"| {leaf_number} | {f['ordinal']} | {f['status']} | {md_cell(scope)} | "
            f"{md_cell(f['verbatim'])} | {md_cell(explain_filter(f['verbatim'], f['status']))} |"
        )

    if not filter_rows:
        filter_rows.append("| 1 | ? | Needs review | root | (no filters extracted) | Empty condition tree ? needs review. |")

    fm = "\n".join(
        [
            "---",
            f"scan_id: {parsed['scan_id']}",
            f"scan_name: {yaml_escape(parsed['scan_name'])}",
            f"source_url: {parsed['source_url']}",
            "market: Indian equities",
            f"horizon: {yaml_escape(horizon)}",
            f"classification: {json.dumps(methods, ensure_ascii=False)}",
            f"tags: {json.dumps(tags, ensure_ascii=False)}",
            f"captured_at: \"{parsed['captured_at']}\"",
            f"enabled_filter_count: {parsed['enabled_filter_count']}",
            f"disabled_filter_count: {parsed['disabled_filter_count']}",
            f"needs_review_filter_count: {parsed['needs_review_count']}",
            f"root_segment: {yaml_escape(parsed['root_segment'])}",
            f"root_join: {yaml_escape(parsed['root_join'])}",
            f"primary_classification: {yaml_escape(primary)}",
            "---",
        ]
    )

    body = f"""# {parsed['scan_name']}

## Source

- Chartink URL: {parsed['source_url']}
- Scan ID: `{parsed['scan_id']}`
- Slug: `{parsed['slug']}`
- Captured: {parsed['captured_at']}
- Market: Indian equities
- Intended horizon: {horizon}
- Created at (Chartink): {parsed.get('created_at')}
- Private: {parsed.get('is_private')}
- Favourite flag: {parsed.get('is_favourite')}
- Alert present flag: {parsed.get('is_alert_present')}
- Raw snapshot: [source-snapshots/{parsed['scan_id']}.json](../source-snapshots/{parsed['scan_id']}.json)
- Text snapshot: [source-snapshots/{parsed['scan_id']}.txt](../source-snapshots/{parsed['scan_id']}.txt)

## What this scan is for

{write_purpose(parsed, methods, horizon)}

## Source-faithful rendered filter tree

```text
{parsed['verbatim_definition']}
```

## Filter status and interpretation

| # | Source-tree position | Status | Group scope | Filter rendering | What it calculates / means |
|---:|---:|---|---|---|---|
{chr(10).join(filter_rows)}

## How the enabled logic works

{write_enabled_logic(parsed)}

## Disabled filters

{write_disabled_section(parsed)}

## Calculation notes

{calc}

## How to use it

{write_how_to_use(parsed, horizon, methods)}

## Strengths

{write_strengths(parsed, methods)}

## Limitations and false-signal risks

{write_limitations(parsed, methods)}

## Classification and related concepts

{write_classification_section(parsed, horizon, methods, tags)}
"""
    return fm + "\n\n" + body


# ---------------------------------------------------------------------------
# Build + QA
# ---------------------------------------------------------------------------


def write_snapshots(parsed: dict) -> None:
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    sid = parsed["scan_id"]
    # immutable-ish raw package
    payload = {
        "captured_at": parsed["captured_at"],
        "scan_id": sid,
        "scan_name": parsed["scan_name"],
        "slug": parsed["slug"],
        "source_url": parsed["source_url"],
        "description": parsed.get("description"),
        "created_at": parsed.get("created_at"),
        "is_private": parsed.get("is_private"),
        "is_favourite": parsed.get("is_favourite"),
        "is_alert_present": parsed.get("is_alert_present"),
        "atlas_query": parsed.get("atlas_query"),
        "atlas_json": parsed.get("atlas_json"),
        "derived": {
            "root_segment": parsed["root_segment"],
            "root_join": parsed["root_join"],
            "root_combination": parsed["root_combination"],
            "root_measurevalue": parsed["root_measurevalue"],
            "enabled_filter_count": parsed["enabled_filter_count"],
            "disabled_filter_count": parsed["disabled_filter_count"],
            "filters": [
                {
                    "ordinal": f["ordinal"],
                    "kind": f["kind"],
                    "status": f["status"],
                    "group_path": f.get("group_path"),
                    "verbatim": f["verbatim"],
                    "segment": f.get("segment"),
                    "join": f.get("join"),
                }
                for f in parsed["filters"]
            ],
            "timeframes_raw": parsed["timeframes_raw"],
        },
    }
    (SNAP_DIR / f"{sid}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (SNAP_DIR / f"{sid}.txt").write_text(
        parsed["verbatim_definition"] + "\n", encoding="utf-8"
    )


def build_index(rows: list[dict]) -> str:
    total = len(rows)
    en_sum = sum(r["enabled_filter_count"] for r in rows)
    dis_sum = sum(r["disabled_filter_count"] for r in rows)
    needs = sum(1 for r in rows if r["needs_review_count"] or r["enabled_filter_count"] == 0)
    by_horizon = Counter(r["horizon"] for r in rows)
    by_method = Counter(r["primary"] for r in rows)

    lines = [
        "# Chartink Scan Wiki",
        "",
        "This knowledge base documents the Chartink scans exactly as captured from the",
        "account dashboard export (`data/exports/all_scans_raw.json`). It covers Indian-equity",
        "scans used for intraday, swing, and positional workflows.",
        "",
        "## Preservation rules",
        "",
        "Each scan page preserves the source scan separately from its analysis:",
        "",
        "- The `Source-faithful rendered filter tree` is a deterministic rendering of `atlas_json`,",
        "  preserving every condition in display order with explicit enabled/disabled labels.",
        "  `atlas_query` is shown separately as the literal compiled active query and can omit disabled filters.",
        "- Raw captures live under [`source-snapshots/`](source-snapshots/) (`.json` + `.txt`).",
        "- Interpretation never alters the captured definition.",
        "",
        "## Reconciliation",
        "",
        f"| Metric | Count |",
        f"|---|---:|",
        f"| Dashboard / export total | {DASHBOARD_TOTAL} |",
        f"| Inventoried scans | {total} |",
        f"| Wiki pages generated | {total} |",
        f"| Raw source snapshots | {total} |",
        f"| Fully documented (page + snapshot) | {total} |",
        f"| Total enabled leaf filters | {en_sum} |",
        f"| Total disabled leaf filters | {dis_sum} |",
        f"| Scans with zero enabled leaves or needs-review rows | {needs} |",
        f"| Inaccessible scans | 0 |",
        "",
        "### Horizon distribution",
        "",
        "| Horizon | Scans |",
        "|---|---:|",
    ]
    for h, c in by_horizon.most_common():
        lines.append(f"| {h} | {c} |")
    lines += [
        "",
        "### Primary method distribution",
        "",
        "| Primary classification | Scans |",
        "|---|---:|",
    ]
    for m, c in by_method.most_common():
        lines.append(f"| {m} | {c} |")

    lines += [
        "",
        "## Scan index",
        "",
        "| ID | Scan | Horizon | Primary classification | Enabled | Disabled | Source |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for r in rows:
        link = f"[{md_cell(r['scan_name'])}](scans/{r['filename']})"
        src = f"[Chartink]({r['source_url']})"
        lines.append(
            f"| {r['scan_id']} | {link} | {r['horizon']} | {r['primary']} | "
            f"{r['enabled_filter_count']} | {r['disabled_filter_count']} | {src} |"
        )

    lines += [
        "",
        "## Classification vocabulary",
        "",
        "- Horizon: Intraday, Swing, Positional, Multi-horizon, Unspecified",
        "- Method: Breakout, Trend following, Momentum, Mean reversion, Volume/",
        "  delivery, Price action, Moving average, Oscillator, Volatility,",
        "  Support/resistance, Fundamental, Multi-factor, or Other",
        "- Context tags: long/short bias, market-cap or liquidity universe, index/stock",
        "  universe, and indicator families used",
        "",
        "## Page format",
        "",
        "Use [the scan template](_template.md) structure. Capture protocol: [_capture-protocol.md](_capture-protocol.md).",
        "",
        f"QA report: [QA_REPORT.md](QA_REPORT.md)",
        "",
        f"Generated: {datetime.now(IST).isoformat()}",
        "",
    ]
    return "\n".join(lines)


def run_qa(parsed_list: list[dict], rows: list[dict], raw_scans: list[dict]) -> str:
    """Verify raw export -> snapshot -> page tree -> leaf-only table."""
    issues: list[str] = []
    ids = [p["scan_id"] for p in parsed_list]
    raw_by_id = {raw.get("id"): raw for raw in raw_scans}
    if len(ids) != len(set(ids)):
        issues.append("CRITICAL: duplicate scan IDs in inventory")
    if len(parsed_list) != DASHBOARD_TOTAL:
        issues.append(f"CRITICAL: inventory count {len(parsed_list)} != dashboard total {DASHBOARD_TOTAL}")

    missing_pages, missing_snap = [], []
    invalid_source, snapshot_mismatch, page_mismatch, table_mismatch = [], [], [], []
    source_valid = snapshot_ok = page_tree_ok = query_ok = leaf_table_ok = 0

    for p in parsed_list:
        sid = p["scan_id"]
        raw = raw_by_id.get(sid)
        if raw is None:
            invalid_source.append((sid, "missing raw record"))
            continue
        try:
            raw_atlas = json.loads(raw.get("atlas_json") or "")
            root = raw_atlas.get("group")
            if not isinstance(root, dict) or root.get("type") != 3:
                raise ValueError("missing type-3 root group")
            source_valid += 1
        except (json.JSONDecodeError, AttributeError, ValueError) as exc:
            invalid_source.append((sid, str(exc)))
            continue

        snap_path = SNAP_DIR / f"{sid}.json"
        text_path = SNAP_DIR / f"{sid}.txt"
        if not snap_path.exists() or not text_path.exists():
            missing_snap.append(sid)
            continue
        snap = load_json(snap_path)
        exact_snapshot = (
            snap.get("scan_id") == raw.get("id")
            and snap.get("scan_name") == raw.get("name")
            and snap.get("slug") == raw.get("slug")
            and snap.get("atlas_query") == raw.get("atlas_query")
            and snap.get("atlas_json") == raw_atlas
        )
        if exact_snapshot:
            snapshot_ok += 1
        else:
            snapshot_mismatch.append((sid, "identity/query/tree differs from raw export"))

        page_path = SCANS_DIR / page_filename(sid, p["scan_name"])
        if not page_path.exists():
            missing_pages.append(sid)
            continue
        page = page_path.read_text(encoding="utf-8")
        tree_header = "## Source-faithful rendered filter tree"
        if tree_header not in page:
            page_mismatch.append((sid, "missing rendered tree header"))
            continue
        tree_tail = page.split(tree_header, 1)[1]
        block = re.search(r"\n\n.{3}text\n(.*?)\n.{3}", tree_tail, re.S)
        if not block:
            page_mismatch.append((sid, "missing rendered tree block"))
            continue
        snapshot_text = text_path.read_text(encoding="utf-8").strip()
        if block.group(1).strip() == snapshot_text:
            page_tree_ok += 1
        else:
            page_mismatch.append((sid, "page tree differs from text snapshot"))
        literal_query = str(raw.get("atlas_query") or "").strip()
        if not literal_query or literal_query in block.group(1):
            query_ok += 1
        else:
            page_mismatch.append((sid, "literal atlas_query absent from page tree"))

        table = re.search(r"## Filter status and interpretation\n\n(.*?)\n## How the enabled logic works", page, re.S)
        if not table:
            table_mismatch.append((sid, "missing leaf-only table"))
            continue
        valid_rows = True
        for leaf_number, f in enumerate(p["conditions"], 1):
            prefix = f"| {leaf_number} | {f['ordinal']} | {f['status']} |"
            if prefix not in table.group(1):
                valid_rows = False
                table_mismatch.append((sid, f"missing/misordered leaf {leaf_number}"))
                break
        if valid_rows:
            leaf_table_ok += 1

    names = [r["filename"] for r in rows]
    if len(names) != len(set(names)):
        issues.append("CRITICAL: duplicate filenames")
    problems = issues + [f"missing page: {sid}" for sid in missing_pages] + [f"missing snapshot: {sid}" for sid in missing_snap] + [f"invalid source {item}" for item in invalid_source] + [f"snapshot mismatch {item}" for item in snapshot_mismatch] + [f"page mismatch {item}" for item in page_mismatch] + [f"table mismatch {item}" for item in table_mismatch]
    lines = [
        "# Scan Wiki QA Report", "", f"Generated: {datetime.now(IST).isoformat()}", "",
        "## Independent source-to-page verification", "",
        f"- Exact export SHA-256: {sha256_file(RAW_PATH)}",
        f"- Valid raw atlas_json root groups: {source_valid}/{len(parsed_list)}",
        f"- Snapshots matching raw identity, query, and tree: {snapshot_ok}/{len(parsed_list)}",
        f"- Pages whose rendered tree equals text snapshot: {page_tree_ok}/{len(parsed_list)}",
        f"- Pages containing literal raw atlas_query: {query_ok}/{len(parsed_list)}",
        f"- Leaf-only tables with ordered source positions: {leaf_table_ok}/{len(parsed_list)}", "",
        "## Inventory reconciliation", "", f"- Export scans: {len(parsed_list)}", f"- Expected dashboard total: {DASHBOARD_TOTAL}", f"- Match: {'YES' if len(parsed_list) == DASHBOARD_TOTAL else 'NO'}", f"- Unique IDs: {len(set(ids))}", f"- Unique filenames: {len(set(names))}", "",
        "## Counts", "", f"- Total enabled leaf filters: {sum(p['enabled_filter_count'] for p in parsed_list)}", f"- Total disabled leaf filters: {sum(p['disabled_filter_count'] for p in parsed_list)}", f"- Scans containing >=1 disabled filter: {sum(1 for p in parsed_list if p['disabled_filter_count'])}", f"- Scans with zero enabled leaves: {sum(1 for p in parsed_list if p['enabled_filter_count'] == 0)}", "",
        "## Representation notes", "", "- The rendered filter tree is a deterministic, source-faithful rendering of exported atlas_json; it is not claimed to be a character-for-character copy of the Chartink UI.", "- atlas_query is shown literally from the export as Chartink's compiled active query. It can omit disabled conditions.", "- Visual UI details not present in the export, such as sorting state, are not invented.", "",
        "## Issues", "",
    ]
    lines.extend(f"- {problem}" for problem in problems[:50]) if problems else lines.append("No source-to-page mismatches found.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    if not RAW_PATH.exists():
        print(f"Missing {RAW_PATH}", file=sys.stderr)
        return 1

    print("Loading exports...")
    raw_scans = load_json(RAW_PATH)
    custom = load_custom_indicators()
    watchlists = load_watchlists()
    print(f"scans={len(raw_scans)} custom_indicators={len(custom)} watchlist_entries={len(watchlists)}")

    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    SNAP_DIR.mkdir(parents=True, exist_ok=True)

    parsed_list: list[dict] = []
    rows: list[dict] = []

    for i, raw in enumerate(raw_scans, 1):
        parsed = parse_scan(raw, custom, watchlists)
        write_snapshots(parsed)
        page = render_page(parsed, custom)
        fn = page_filename(parsed["scan_id"], parsed["scan_name"])
        (SCANS_DIR / fn).write_text(page, encoding="utf-8")
        horizon = classify_horizon(parsed)
        methods = classify_methods(parsed)
        rows.append(
            {
                "scan_id": parsed["scan_id"],
                "scan_name": parsed["scan_name"],
                "source_url": parsed["source_url"],
                "filename": fn,
                "horizon": horizon,
                "primary": methods[0] if methods else "Other",
                "enabled_filter_count": parsed["enabled_filter_count"],
                "disabled_filter_count": parsed["disabled_filter_count"],
                "needs_review_count": parsed["needs_review_count"],
            }
        )
        parsed_list.append(parsed)
        if i % 50 == 0 or i == len(raw_scans):
            print(f"  processed {i}/{len(raw_scans)}")

    index_md = build_index(rows)
    (WIKI / "README.md").write_text(index_md, encoding="utf-8")
    print("Wrote wiki index")

    qa = run_qa(parsed_list, rows, raw_scans)
    QA_PATH.write_text(qa, encoding="utf-8")
    print("Wrote QA report")
    print(qa.split("## Issues")[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
