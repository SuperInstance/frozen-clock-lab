"""Seeded op-stream runner: N deterministic ops through a ReceiptChain under
a chosen clock fault. Writes receipts.txt (hash op per line),
clock_values.txt, and time_nonmonotonic.txt for forensics."""
import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lab.chain import ReceiptChain
from lab.clock import SimClock


def gen_ops(seed, n):
    rng = random.Random(seed)
    words = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]
    return [f"{rng.choice(words)}-{rng.getrandbits(32):08x}" for _ in range(n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--clock", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    clock = SimClock(a.clock)
    chain = ReceiptChain()
    receipts = []
    clocks = []
    for op in gen_ops(a.seed, a.n):
        receipts.append(chain.append(op))
        clocks.append(clock.now())

    with open(os.path.join(a.out, "receipts.txt"), "w") as f:
        for (pos, op, r), t in zip(chain.ops, clocks):
            f.write(f"{r} {op}\n")
    with open(os.path.join(a.out, "clock_values.txt"), "w") as f:
        for t in clocks:
            f.write(f"{t}\n")
    with open(os.path.join(a.out, "time_nonmonotonic.txt"), "w") as f:
        for p in clock.nonmonotonic_positions:
            f.write(f"{p}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
