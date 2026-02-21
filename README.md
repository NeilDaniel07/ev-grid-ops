# EV Grid Ops

**Built for the Texas Venture Group × c0mpiled Hackathon (UT Austin)**

EV Grid Ops helps EV charging operators answer one costly question:

**“Should we dispatch a technician now, or verify first?”**

Most systems triage by severity alone.  
We add a **certainty layer** so operators can avoid unnecessary truck rolls without missing real failures.

## The Problem

Charging networks produce constant alerts: offline chargers, payment errors, network timeouts, reboots, and degraded performance.

Operators are forced into a bad tradeoff:
- Dispatch too aggressively → wasted field operations cost
- Dispatch too conservatively → charger downtime and poor driver experience

## Our Solution

EV Grid Ops compares two approaches side by side:

1. **Baseline Triage**
   - Prioritizes incidents from severity signals
   - Recommends action directly

2. **Certainty-Aware Triage**
   - Scores severity **and confidence**
   - Explains uncertainty
   - Triggers a quick verification step when confidence is low
   - Dispatches only when evidence is strong

This creates a practical decision loop:
**Triage → Confidence Check → Verify if needed → Dispatch with higher certainty**

## Why It Matters

Every unnecessary truck roll costs money and slows response capacity.  
By introducing structured verification for uncertain cases, operators can:
- Reduce false dispatches
- Preserve technician bandwidth for critical issues
- Improve uptime consistency across charger networks

## Demo Story (Judge-Friendly)

In the demo, both systems receive the same incident stream:
- Baseline dispatches based on severity only
- Certainty-aware triage pauses uncertain cases for verification
- Verified true issues are dispatched
- False alarms are filtered out

Result: **fewer unnecessary dispatches with strong operational coverage**

## What Makes This Stand Out

- Clear business value tied to operating cost
- Explainable decisions (not black-box outputs)
- Built for real operator workflows, not a toy chatbot
- Focused MVP that proves a concrete economic lever

## Team

- **Aditya Patwardhan** — Member 1: Data, API state, case lifecycle, metrics
- **Neil Daniel** — Member 2: Baseline + certainty triage engine and scoring logic
- **Andrew Manoni** — Member 3: Frontend dashboard, compare UX, dispatch/verify actions

## Hackathon Context

This project was built in a fast execution environment with real constraints, mentorship from YC founders, and a focus on shipping practical AI + infrastructure tools for energy and urban systems.
