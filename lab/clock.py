"""SimClock — wall time as an injectable fault, not a fact.

Modes: honest | freeze | skew:<rate> | replay
Deterministic: given the same tick sequence, now() is fully reproducible.
The clock NEVER feeds the receipt chain; it is recorded alongside for
forensics only.
"""


class SimClock:
    def __init__(self, mode="honest", t0=1_000_000):
        self.mode = mode
        self.t0 = t0
        self.tick_count = 0
        self.last_t = None
        self.nonmonotonic_positions = []  # positions where time went backward

    def now(self):
        n = self.tick_count
        if self.mode == "honest":
            t = self.t0 + n
        elif self.mode == "freeze":
            t = self.t0
        elif self.mode.startswith("skew:"):
            rate = int(self.mode.split(":", 1)[1])
            t = self.t0 + n * rate
        elif self.mode == "replay":
            # cycle of 50 forward then reset 40 back — guaranteed backward moves
            t = self.t0 + (n % 50) - 40 * (n // 50)
        else:
            raise ValueError(f"unknown clock mode: {self.mode}")
        if self.last_t is not None and t < self.last_t:
            self.nonmonotonic_positions.append(n)
        self.last_t = t
        self.tick_count += 1
        return t
