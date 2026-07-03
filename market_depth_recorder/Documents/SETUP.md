# Setup — Market Depth Recorder

Standalone service with its own venv and `requirements.txt` (§1.3, §2.1). **Not** coupled to the
OpenAlgo platform's `uv` environment.

## Bootstrap (from the parent `SS_Projects/`)

```bash
# 1. Create + activate a dedicated venv
python -m venv .venv
# Windows (Git Bash):   source .venv/Scripts/activate
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# macOS / Linux:        source .venv/bin/activate

# 2. Install pinned dependencies
pip install -r market_depth_recorder/requirements.txt
```

`requirements.txt` pins `openalgo==2.0.2` **exactly** (its depth-callback behavior is load-bearing —
see `ARCHITECTURE.md` → Transport) and everything else with a compatible-release `~=` pin.

## Run (always as a module, from `SS_Projects/`)

```bash
# Validate the config (all §7.3 checks; exit 0 valid / 1 invalid)
python -m market_depth_recorder --validate-config --config market_depth_recorder/config.yaml

# Later phases:
python -m market_depth_recorder --preflight --config market_depth_recorder/config.yaml   # P1
python -m market_depth_recorder --status    --config market_depth_recorder/config.yaml   # P6
python -m market_depth_recorder --replay ./data/market_depth_raw_YYYYMMDD.jsonl.gz \
    --config market_depth_recorder/config.yaml --output ./data/....duckdb                 # P7
```

Run from `SS_Projects/` (the package's parent) so `python -m market_depth_recorder` resolves.

## Tests (no live feed required)

```bash
python -m pytest market_depth_recorder/tests/ -q
```

## Configuration

Everything lives in `config.yaml` (§7.1). Every engine constant resolves from it; a missing or
out-of-range value fast-fails at startup with exit code 1 (§7.3). Set `openalgo.api_key` to your real
key before any live run. See `Documents/config.md` for the validation rules.
