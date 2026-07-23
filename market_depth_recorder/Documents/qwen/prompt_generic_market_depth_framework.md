I really like the overall direction we've reached, and I think we've now arrived at the point where we should stop thinking in terms of "how FYERS works" and start thinking in terms of "what a generic market-depth framework should look like."

The protocol investigation is now complete and frozen. I'd like to treat it as a stable foundation and build the framework above it rather than continuing to evolve the protocol layer.

I'd also like to slightly evolve the architecture before we write any implementation code.

---

# Overall Design Philosophy

I don't want the framework to be designed around FYERS.

I want it to be designed around **capabilities**.

FYERS should simply become one broker implementation that advertises its market-data capabilities.

Tomorrow another broker may expose:

- different TBT budgets
- full-chain Level-2
- Level-3
- unlimited depth
- premium feeds
- different subscription semantics

The architecture should remain unchanged.

Only the broker capability description should change.

This principle should drive every design decision.

---

# Overall Build Order

Rather than jumping directly into implementation, I'd like us to design the framework in the following order.

```text
Broker Capabilities
        ↓
Window Manager
        ↓
Priority Policy
        ↓
Depth Allocator
        ↓
Subscription Manager
        ↓
Broker Adapter
```

Each layer should have one clear responsibility.

---

# Phase 1 — Broker Capabilities

I actually think this is the most important piece of the architecture.

The Broker Capability layer becomes the contract between broker implementations and the generic framework.

Everything above this layer should remain completely broker-agnostic.

The rest of the system should never know:

- FYERS
- TBT
- HSM
- channels
- connection limits
- subscription restrictions
- broker-specific quirks

Instead, the framework simply asks:

> "What capabilities do you expose?"

For FYERS today, that might conceptually look like:

```yaml
market_depth:

  supports_hsm: true

  supports_tbt: true

  tbt:

    connections: 3

    symbols_per_connection: 5

    total_budget: 15

    channels: 50

  hsm:

    available: true

exchange_support:

  NFO:
    tbt: true
    hsm: true

  NSE:
    tbt: true

  BFO:
    hsm: true
```

This layer is purely descriptive.

It tells the framework what is available.

It does **not** tell the framework how to use it.

Examples of future broker capability differences:

Broker A

```
TBT Budget = 15
```

Broker B

```
TBT Budget = 40
```

Broker C

```
Unlimited Level-2
```

Broker D

```
Only 10-level depth
```

Nothing above this layer changes.

---

# Phase 2 — Window Manager

The Window Manager has one responsibility:

> **Determine the candidate universe.**

It answers only one question:

> **"Which instruments should be considered right now?"**

It knows nothing about:

- broker capabilities
- TBT
- HSM
- budgets
- priorities
- subscriptions
- websocket management

Given spot price and configuration, it simply determines the active market universe.

For example,

```
Spot = 24025
```

Configuration

```yaml
window_atm_zone:

    radius_points: 300

    strike_step: 50

window_atm_zone_outside:

    radius_points: 1500

    strike_step: 100
```

The Window Manager may return

```
22500
22600
...
23800
23900
23950
24000
24050
24100
24150
24200
24300
...
25500
```

Notice something important.

It does **not** say:

- these should receive TBT
- these should receive HSM
- these are high priority
- these are low priority

It simply defines the current **candidate universe**.

Think of it as drawing the boundary around the market that the rest of the framework is allowed to reason about.

---

# Phase 3 — Priority Policy

(I'd prefer this name over "Allocation Policy" because I think it better describes its responsibility.)

The Priority Policy has one responsibility:

> **Determine which candidates are most important.**

It receives the candidate universe from the Window Manager.

It does **not** allocate anything.

It simply ranks.

Example.

Window Manager returns

```
23900
23950
24000
24050
24100
24150
24200
24300
24400
24500
```

A simple ATM-distance policy may produce

```
Priority

1 → 24000
2 → 24050
3 → 23950
4 → 24100
5 → 23900
6 → 24150
7 → 24200
8 → 24300
9 → 24400
10 → 24500
```

A Gamma policy may produce a completely different ranking.

```
1 → 24100
2 → 24050
3 → 24000
4 → 24200
5 → 23950
...
```

A Volume policy may produce another ranking.

```
1 → 23950
2 → 24000
3 → 24100
...
```

The Priority Policy does not know anything about broker budgets.

It does not know whether the budget is

- 5
- 15
- 40
- unlimited

It simply answers

> **"Among these candidates, which are the most important?"**

Different strategies may plug in different Priority Policies.

Examples include:

- Closest ATM
- Highest Gamma
- Highest Open Interest
- Highest Volume
- Strategy-specific
- Time-of-day aware
- Volatility-aware
- Hybrid scoring models

This makes prioritization completely pluggable.

---

# Phase 4 — Depth Allocator

This is the component that finally consumes the scarce resource.

It answers one question:

> **"Given a limited premium-depth budget, who gets it?"**

It consumes:

- Broker Capabilities
- Candidate Universe
- Priority Ranking

Suppose the Broker Capability says

```
Depth Budget = 15
```

Priority Policy returns

```
Rank 1
Rank 2
...
Rank 40
```

The Depth Allocator simply says

```
Top 15

↓

Premium Depth
```

Everything else

↓

```
Standard Depth
```

Notice something important.

The allocator does **not** decide priority.

The Priority Policy already did that.

The allocator simply applies the available budget.

Likewise, it never knows that FYERS internally uses

```
3 connections

×

5 symbols
```

It only sees

```
Depth Budget = 15
```

The broker implementation hides all connection management.

The allocator should also minimise churn.

Suppose spot moves slightly.

Instead of rebuilding everything, it should:

- retain allocations that are still relevant
- evict only obsolete allocations
- promote newly important strikes

The objective is:

- minimal subscription churn
- maximum stability
- highest market relevance

---

# Phase 5 — Subscription Manager

This becomes the reconciliation engine.

It converts the allocator's desired state into broker operations.

Inputs

```
Desired State

↓

Current State
```

Outputs

```
Subscribe

Unsubscribe

Pause

Resume

Reconnect

Recovery
```

Example

Desired

```
24100 CE

24100 PE

24150 CE
```

Current

```
24100 CE

24050 CE

24100 PE
```

Diff

```
Unsubscribe

24050 CE

Subscribe

24150 CE
```

Only the minimum required changes are executed.

The Subscription Manager should also own:

- reconnect recovery
- session restoration
- resubscription
- reconciliation after disconnects
- batching
- broker-specific sequencing

---

# Broker Adapter

Finally, the Broker Adapter translates generic subscription requests into broker-specific operations.

Only this layer knows:

- FYERS
- TBT
- HSM
- channels
- connection pools
- broker limitations

Everything above remains broker-agnostic.

---

# Separation of Responsibilities

Each component should have one responsibility.

Broker Capabilities

↓

**What can this broker provide?**

Window Manager

↓

**Which instruments belong to the active market universe?**

Priority Policy

↓

**Among those instruments, which are the most important?**

Depth Allocator

↓

**Given the available premium-depth budget, who receives it?**

Subscription Manager

↓

**How do I reconcile desired state with live subscriptions?**

Broker Adapter

↓

**How do I execute those operations for this specific broker?**

This separation keeps every component small, testable, replaceable and easy to reason about.

---

# Why these are separate components

Initially these three components can appear very similar.

However, they solve three fundamentally different problems.

Imagine a college admission process.

## Window Manager

Question:

> Who applied?

Output

```
1000 students
```

It simply builds the candidate list.

---

## Priority Policy

Question:

> How should these students be ranked?

Output

```
Rank 1

Rank 2

Rank 3

...

Rank 1000
```

It doesn't admit anyone.

It only ranks.

---

## Depth Allocator

Question:

> We have only 100 seats.

Who gets admitted?

Output

```
Top 100

↓

Accepted

Remaining

↓

Waiting / Rejected
```

The allocator doesn't perform the ranking.

It simply applies the available budget.

Exactly the same pattern applies here.

Window Manager

↓

Build candidate universe.

Priority Policy

↓

Rank candidates.

Depth Allocator

↓

Allocate premium depth to the highest-ranked candidates.

---

# Trading Example

Spot

```
24025
```

## Step 1 — Window Manager

Produces

```
23900
23950
24000
24050
24100
24150
24200
24300
24400
24500
```

## Step 2 — Priority Policy

Ranks them

```
1 24000 CE
2 24000 PE
3 24050 CE
4 23950 PE
5 24100 CE
6 23900 PE
...
```

## Step 3 — Depth Allocator

Broker Capability

```
Depth Budget = 6
```

Allocator assigns

```
Premium Depth

24000 CE
24000 PE
24050 CE
23950 PE
24100 CE
23900 PE
```

Everything else

```
Standard Depth

24150 CE
24200 CE
24300 PE
24400 CE
24500 PE
```

Notice how every stage has one responsibility.

---

# Overall Architecture

```
Strategies
        │
        ▼
Market Data Framework
        │
        ▼
Broker Capabilities
        │
        ▼
Window Manager
        │
        ▼
Priority Policy
        │
        ▼
Depth Allocator
        │
        ▼
Subscription Manager
        │
        ▼
Broker Adapter
        │
        ▼
FYERS
```

Everything above the Broker Adapter should remain completely broker-agnostic.

Only the Broker Adapter should know implementation details.

---

# Design Expectations

Before writing any implementation code, I'd like us to produce a comprehensive architecture/design document.

I'd like each of these sections to be expanded in detail, including:

- responsibilities
- ownership boundaries
- interfaces
- lifecycle
- configuration
- state management
- threading model
- interaction diagrams
- sequence diagrams
- failure modes
- recovery mechanisms
- reconciliation strategy
- extension points
- testing strategy
- migration strategy
- worked execution examples
- configuration examples
- edge cases
- performance considerations
- trade-offs
- rationale for every major design decision

Essentially, I'd like us to treat this as a proper architecture phase rather than an implementation phase.

Once that document is reviewed and agreed upon, we can proceed with implementation using the same architecture-first, review-gated engineering discipline we've followed throughout this project.
