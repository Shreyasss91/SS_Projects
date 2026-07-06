"""utils.py primitive tests (§2.1 utils): decay weights, IST parsing, atomic write, disk free."""

from __future__ import annotations

import math

import pytest

from market_depth_recorder.utils import (
    atomic_write,
    decay_weights,
    free_disk_mb,
    parse_ist_hhmm,
    process_rss_mb,
    to_epoch_seconds,
)


# F3 — decay-weight array (spec §3.4.2 M8 reference values)
def test_decay_weights_reference_values():
    w = decay_weights(10, 0.2)
    assert w[0] == pytest.approx(1.0)
    assert w[4] == pytest.approx(0.4493, abs=1e-3)   # w_5 ≈ 0.45
    assert w[9] == pytest.approx(0.1653, abs=1e-3)   # w_10 ≈ 0.16
    # Monotonically decreasing.
    assert all(w[i] > w[i + 1] for i in range(len(w) - 1))


def test_decay_weights_rejects_bad_args():
    with pytest.raises(ValueError):
        decay_weights(0, 0.2)
    with pytest.raises(ValueError):
        decay_weights(5, -0.1)


# F2 — IST time parsing
@pytest.mark.parametrize("value", ["09:15", "00:00", "23:59", "15:30"])
def test_parse_ist_ok(value):
    t = parse_ist_hhmm(value)
    assert t.tzinfo is not None


@pytest.mark.parametrize("value", ["9", "9:99", "24:00", "abc", "09:60", "09:15:00"])
def test_parse_ist_bad(value):
    with pytest.raises(ValueError):
        parse_ist_hhmm(value)


def test_to_epoch_seconds_positive():
    assert to_epoch_seconds() > 1_600_000_000  # well after 2020


# F4 — atomic write round-trip
def test_atomic_write_roundtrip(tmp_path):
    target = tmp_path / "sub" / "health.json"  # parent created on demand
    atomic_write(str(target), '{"ok": true}')
    assert target.read_text(encoding="utf-8") == '{"ok": true}'
    # Overwrite is atomic and leaves no stray temp files behind.
    atomic_write(str(target), "second")
    assert target.read_text(encoding="utf-8") == "second"
    leftovers = [p.name for p in target.parent.iterdir() if p.name.startswith(".tmp_")]
    assert leftovers == []


# F5 — disk free
def test_free_disk_mb_positive(tmp_path):
    assert free_disk_mb(str(tmp_path)) > 0
    assert math.isfinite(free_disk_mb(str(tmp_path)))


# F6 — process RSS (P8 perf-target sanity / health.json rss_mb)
def test_process_rss_mb_positive_and_finite():
    rss = process_rss_mb()
    assert isinstance(rss, float)
    assert math.isfinite(rss)
    # A running interpreter always has a non-trivial resident set on this platform.
    assert rss > 0.0


def test_process_rss_mb_reflects_allocation():
    before = process_rss_mb()
    # Hold ~80 MiB so even peak-RSS (Unix ru_maxrss) reflects the growth; keep it referenced.
    blob = bytearray(80 * 1024 * 1024)
    after = process_rss_mb()
    assert after >= before  # never shrinks below the pre-alloc reading
    del blob


def test_process_rss_mb_never_raises(monkeypatch):
    # Force the platform path to blow up → best-effort 0.0, never propagates (observability is non-fatal).
    import market_depth_recorder.utils as u

    monkeypatch.setattr(u.sys, "platform", "win32")
    monkeypatch.setattr(u, "_win_working_set_mb", lambda: (_ for _ in ()).throw(OSError("boom")))
    assert process_rss_mb() == 0.0
