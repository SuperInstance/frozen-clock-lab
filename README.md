# frozen-clock-lab

**Order lives in the chain, not in time.** A fault-injection lab where a
deterministic op-stream hangs from an fnv1a-64 receipt chain and wall-clock
is an *injectable fault* — freeze, skew, replay, or honest — so you can prove
which properties survive which faults.

Origin (real, 2026-10-02): an edge worker's clock froze and lied across
25.6M operations while chained receipts kept every result intact. Nothing
broke, because nothing that mattered had ever trusted the clock. This lab
generalizes that accident from anecdote into instrument.

## Doctrine

- A receipt is `fnv1a64(prev_receipt || "|" || op)`. Position is an integer
  index — never a time.
- The clock is recorded alongside for **forensics only**. It never feeds the
  chain. A frozen clock changes nothing about correctness; a replayed clock
  leaves `time_nonmonotonic` positions as evidence, not damage.
- Syncing two simulators means syncing **by position**, not by timestamp.

## What the lab proves (pins P1–P6b)

| pin | claim |
|-----|-------|
| P1 | chain-survives-freeze: 10k ops under a frozen clock produce byte-identical receipts to an honest run (same seed) |
| P2 | order-not-time: two streams with the same ops in different order diverge at the first differing position |
| P3 | replay-detected: clock resets mid-stream → chain still verifies, and the exact backward positions are named |
| P4 | skew-reconciled: two simulators with wildly different skews produce identical receipts at identical positions |
| P5 | genesis-anchor: replaying from a saved mid-stream receipt recomputes forward to the identical terminal receipt |
| P6 | sig-canonical: the raw fnv1a-64 compression function is pinned to reference vectors, so substituting the prime, offset basis, xor/multiply order, or mask cannot pass silently |
| P6b | construction-canonical: the receipt construction itself (genesis basis encoding, "\|" separator, lowercase zero-padded `%016x` wire form, and `verify()`) is pinned to known-answer chain vectors — closing the separator/hex-case substitutions that passed all of P1–P6 (guardian lane F', 2026-10-02) |

Run: `python3 tests/pins_clock.py` (stdlib only; FAIL-first log in
`pins/failfirst.log`).

## What the lab refuses to claim (honest limits)

1. The chain proves **order**, not **importance** — a perfectly-ordered log
   of garbage is still garbage. Receipts don't judge content.
2. fnv1a-64 is an integrity mark, not a signature — collision resistance is
   not cryptographic. A keyed/sig variant is a future increment.
3. Replay *detection* here means the clock log shows it; a chain that
   consults the clock would behave differently — the lab's whole point is
   that you don't build that chain.
4. `replay` mode is one reset shape (50-forward/40-back); other fault
   shapes (NTP-slew, leap-second, dual-clock disagreement) are unbuilt.
5. The lab is single-process. Cross-process order without a shared clock
   (vector clocks, CRDTs) is a different, harder lab.
