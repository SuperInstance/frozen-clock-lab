#!/usr/bin/env python3
"""PINS P1-P5 for frozen-clock-lab. FAIL-first: run against absent lab/ -> log."""
import sys, os, subprocess, shutil, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

results = []
def pin(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))

def run_stream(seed, n, clock, script=ROOT):
    """helper: build a stream via lab.stream CLI and return its state dir path"""
    d = tempfile.mkdtemp(prefix="fcl-")
    r = subprocess.run([sys.executable, os.path.join(script, "lab", "stream.py"),
                        "--seed", str(seed), "--n", str(n), "--clock", clock,
                        "--out", d], capture_output=True, text=True)
    return d, r

try:
    from lab.clock import SimClock
    from lab.chain import ReceiptChain
    from lab import stream as streamlib
    LAB = True
except ModuleNotFoundError as e:
    LAB = False
    with open(os.path.join(ROOT, "pins", "failfirst.log"), "w") as f:
        f.write(f"FAIL-first: lab/ absent — {e}\n")

def main():
    if not LAB:
        for p in ["P1", "P2", "P3", "P4", "P5"]:
            pin(p, False, "lab/ not importable")
        return 1

    # P1: chain survives freeze — frozen-clock run byte-identical to honest run
    d1, _ = run_stream(20261002, 10000, "honest")
    d2, _ = run_stream(20261002, 10000, "freeze")
    h1 = open(os.path.join(d1, "receipts.txt")).read()
    h2 = open(os.path.join(d2, "receipts.txt")).read()
    pin("P1 chain-survives-freeze", h1 == h2 and len(h1.splitlines()) == 10000,
        f"identical={h1 == h2} lines={len(h2.splitlines())}")
    shutil.rmtree(d1); shutil.rmtree(d2)

    # P2: order-not-time — two streams, same ops different order -> first divergence
    from lab.chain import ReceiptChain, fnv1a64
    a = ReceiptChain(); b = ReceiptChain()
    ops_a = ["alpha", "beta", "gamma"]; ops_b = ["alpha", "gamma", "beta"]
    div = None
    for i, (oa, ob) in enumerate(zip(ops_a, ops_b)):
        ra = a.append(oa); rb = b.append(ob)
        if ra != rb and div is None:
            div = i
    pin("P2 order-not-time", div == 1, f"first-divergence-position={div}")

    # P3: replay detected — clock moves backward mid-stream, chain still verifies,
    #     time_nonmonotonic warnings name the exact positions
    d3, _ = run_stream(7, 200, "replay")
    warns = open(os.path.join(d3, "time_nonmonotonic.txt")).read().splitlines()
    # recompute verification independently
    receipts = open(os.path.join(d3, "receipts.txt")).read().splitlines()
    ch = ReceiptChain()
    ok = all(ch.append(line.split(" ", 1)[1] if " " in line else "") == line.split()[0]
             for line in receipts) if receipts else False
    pin("P3 replay-detected", ok and len(warns) > 0,
        f"chain-verifies={ok} nonmonotonic-positions={len(warns)}")
    shutil.rmtree(d3)

    # P4: skew reconciled — two skewed simulators, same seed, same receipts
    d4, _ = run_stream(99, 500, "skew:1000")
    d5, _ = run_stream(99, 500, "skew:99999")
    r4 = open(os.path.join(d4, "receipts.txt")).read()
    r5 = open(os.path.join(d5, "receipts.txt")).read()
    pin("P4 skew-reconciled", r4 == r5 and len(r4.splitlines()) == 500)
    shutil.rmtree(d4); shutil.rmtree(d5)

    # P5: genesis anchor — replay from a saved mid-stream receipt forward
    d6, _ = run_stream(4242, 300, "honest")
    lines = open(os.path.join(d6, "receipts.txt")).read().splitlines()
    anchor_line = lines[149]  # position 149 (0-based), the 150th op
    anchor_hash, anchor_op = anchor_line.split(" ", 1)
    ch2 = ReceiptChain(genesis=anchor_hash)
    for line in lines[150:]:
        h, op = line.split(" ", 1)
        rh = ch2.append(op)
        if rh != h:
            pin("P5 genesis-anchor", False, "diverged after anchor at replayed pos")
            return 1
    terminal = lines[-1].split()[0]
    pin("P5 genesis-anchor", ch2.head == terminal,
        f"replayed-forward-to-terminal={ch2.head == terminal}")
    shutil.rmtree(d6)

    return 0 if all(ok for _, ok, _ in results) else 1

if __name__ == "__main__":
    sys.exit(main())
