"""Unit tests for the F8 bridge itself (``framework_bridge.py``, Plan_002 §20).

The integration suite drives the bridge through the real orchestrator and the real adapter. These
tests drive it through stubs instead, so the bridge's own decisions — what it publishes, what it
consumes, and what it refuses to let escape — are visible on their own.
"""

from __future__ import annotations

import pytest

from market_depth_recorder.framework_bridge import (
    FrameworkBridge,
    LatestWinsMailbox,
    Observation,
)
from market_depth_recorder.market_depth_framework import (
    DepthType,
    Instrument,
    SubscriptionAction,
    SubscriptionPlan,
)
from market_depth_recorder.market_depth_framework.orchestrator import (
    FrameworkOrchestrator,
    RebalanceResult,
)
from market_depth_recorder.market_depth_framework.subscription_state import ActionKind

LEG = Instrument(
    underlying="ALPHA", exchange="XFO", symbol="ALPHA25000CE",
    expiry="30-DEC-99", strike=25000.0, option_type="CE",
)


class FakeClock:
    def __init__(self, t: float = 100.0):
        self.t = t

    def __call__(self) -> float:
        return self.t


class StubOrchestrator(FrameworkOrchestrator):
    """A scripted orchestrator: the bridge is the thing under test, not the pass.

    A real subclass, because the bridge type-checks what it is handed — that guard is the reason a
    misconfigured pipeline fails at construction rather than at the first tick, and it stays.
    """

    def __init__(self, results):  # noqa: D107 — deliberately does not run the real construction
        self.results = list(results)
        self.calls: list[tuple] = []
        self.resets = 0
        self._desired: dict = {}

    # The real class exposes these as read-only properties over its capability layer.
    @property
    def effective_budget(self) -> int:
        return 7

    @property
    def eligible(self) -> frozenset:
        return frozenset({"ALPHA"})

    def rebalance(self, spots, live, *, rejected=(), trigger=None):
        self.calls.append((dict(spots), dict(live), tuple(rejected), trigger))
        return self.results.pop(0) if self.results else None

    def desired(self) -> dict:
        return dict(self._desired)

    def reset(self) -> None:
        self.resets += 1


def action(kind: ActionKind = ActionKind.SUBSCRIBE, tier: DepthType = DepthType.STANDARD):
    return SubscriptionAction(instrument=LEG, kind=kind, depth=tier)


def result(plan: SubscriptionPlan, *, trigger: str = "interval", at: float = 100.0):
    return RebalanceResult(
        plan=plan, desired={LEG: DepthType.STANDARD}, windows=(), budgets={}, trigger=trigger, at=at
    )


def bridge(results, clock=None) -> tuple[FrameworkBridge, StubOrchestrator]:
    orch = StubOrchestrator(results)
    return FrameworkBridge(orch, clock=clock or FakeClock()), orch


# --------------------------------------------------------------------------------------------------
# Publishing
# --------------------------------------------------------------------------------------------------
def test_a_pass_with_actions_publishes_one_envelope():
    b, _ = bridge([result(SubscriptionPlan(added_new=(action(),)))])
    envelope = b.maybe_rebalance({"ALPHA": 25000.0})
    assert envelope is not None
    assert envelope.sequence == 1
    assert envelope.trigger == "interval"
    assert dict(envelope.desired) == {LEG: DepthType.STANDARD}
    assert b.plans.take() is envelope


def test_a_pass_that_did_not_run_publishes_nothing():
    b, _ = bridge([None])
    assert b.maybe_rebalance({"ALPHA": 25000.0}) is None
    assert b.plans.pending is False
    assert b.stats()["passes"] == 0


def test_an_empty_plan_never_evicts_a_plan_feed_has_not_executed():
    """Publishing an empty plan would supersede a pending one while carrying no action of its own."""
    real = result(SubscriptionPlan(added_new=(action(),)))
    empty = result(SubscriptionPlan(), trigger="interval")
    b, _ = bridge([real, empty])
    first = b.maybe_rebalance({"ALPHA": 25000.0})
    assert b.maybe_rebalance({"ALPHA": 25000.0}) is None  # the empty pass
    assert b.plans.pending is True
    assert b.plans.take() is first  # the unexecuted plan survived
    assert b.stats()["passes"] == 2  # ...and the pass itself still counted


# --------------------------------------------------------------------------------------------------
# The reverse channel
# --------------------------------------------------------------------------------------------------
def test_an_observation_is_consumed_by_the_next_pass():
    b, orch = bridge([result(SubscriptionPlan(added_new=(action(),)))])
    b.publish_observation({LEG: DepthType.PREMIUM})
    b.maybe_rebalance({"ALPHA": 25000.0})
    _spots, live, _rejected, _trigger = orch.calls[0]
    assert live == {LEG: DepthType.PREMIUM}
    assert b.stats()["observations"] == 1


def test_an_absent_observation_means_no_news_not_an_empty_book():
    """FEED publishes when something changed; silence must not read as "every leg died"."""
    b, orch = bridge([
        result(SubscriptionPlan(added_new=(action(),))),
        result(SubscriptionPlan(added_new=(action(),))),
    ])
    b.publish_observation({LEG: DepthType.PREMIUM})
    b.maybe_rebalance({"ALPHA": 25000.0})
    b.maybe_rebalance({"ALPHA": 25000.0})  # no new observation in between
    assert orch.calls[1][1] == {LEG: DepthType.PREMIUM}


def test_rejections_are_handed_over_once():
    b, orch = bridge([
        result(SubscriptionPlan(added_new=(action(),))),
        result(SubscriptionPlan(added_new=(action(),))),
    ])
    b.publish_observation({}, rejections=(LEG,))
    b.maybe_rebalance({"ALPHA": 25000.0})
    assert orch.calls[0][2] == (LEG,)
    b.maybe_rebalance({"ALPHA": 25000.0})
    assert orch.calls[1][2] == ()  # consumed, not replayed forever
    assert b.stats()["pending_rejections"] == 0


def test_a_rejection_survives_a_pass_that_did_not_run():
    b, orch = bridge([None, result(SubscriptionPlan(added_new=(action(),)))])
    b.publish_observation({}, rejections=(LEG,))
    b.maybe_rebalance({"ALPHA": 25000.0})  # no pass ran; nothing consumed it
    assert b.stats()["pending_rejections"] == 1
    b.maybe_rebalance({"ALPHA": 25000.0})
    assert orch.calls[1][2] == (LEG,)


def test_publishing_an_observation_never_raises():
    def bad_clock():
        raise RuntimeError("clock failed")

    b, _ = bridge([], clock=bad_clock)
    b.publish_observation({LEG: DepthType.STANDARD})  # swallowed and logged, never propagated
    assert b.observations.pending is False


def test_an_observation_is_a_whole_snapshot():
    box = LatestWinsMailbox()
    box.publish(Observation(live={LEG: DepthType.PREMIUM}, rejections=(), at=1.0))
    observation = box.take()
    assert observation.live == {LEG: DepthType.PREMIUM}
    assert observation.at == 1.0


# --------------------------------------------------------------------------------------------------
# Fault isolation and lifecycle
# --------------------------------------------------------------------------------------------------
def test_a_rebalance_failure_is_counted_and_contained():
    class Exploding(StubOrchestrator):
        def rebalance(self, *_a, **_k):
            raise RuntimeError("boom")

    b = FrameworkBridge(Exploding([]), clock=FakeClock())
    assert b.maybe_rebalance({"ALPHA": 25000.0}) is None
    stats = b.stats()
    assert stats["failures"] == 1
    assert stats["last_error"].startswith("RuntimeError")


def test_a_reset_failure_is_contained():
    class Exploding(StubOrchestrator):
        def reset(self):
            raise RuntimeError("boom")

    FrameworkBridge(Exploding([]), clock=FakeClock()).reset()  # must not raise


def test_reset_forgets_the_desired_coverage():
    b, orch = bridge([])
    b.reset()
    assert orch.resets == 1


def test_force_rebalance_labels_the_pass():
    b, orch = bridge([result(SubscriptionPlan(added_new=(action(),)), trigger="initial")])
    b.force_rebalance({"ALPHA": 25000.0}, "initial")
    assert orch.calls[0][3] == "initial"


def test_stats_are_json_safe_and_complete():
    b, _ = bridge([result(SubscriptionPlan(added_new=(action(),)))])
    b.maybe_rebalance({"ALPHA": 25000.0})
    stats = b.stats()
    assert set(stats) >= {
        "passes", "plans_published", "failures", "observations", "last_trigger", "last_pass_at",
        "last_error", "effective_budget", "desired_legs", "live_legs", "pending_rejections",
        "eligible_underlyings", "plan_mailbox", "observation_mailbox",
    }
    assert stats["plans_published"] == 1
    assert stats["eligible_underlyings"] == ["ALPHA"]


def test_the_bridge_requires_a_callable_clock():
    with pytest.raises(TypeError):
        FrameworkBridge(StubOrchestrator([]), clock="not callable")
