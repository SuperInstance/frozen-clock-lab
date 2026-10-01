"""fnv1a-64 receipt chain. Order lives here, not in any clock."""

FNV64_OFFSET = 0xcbf29ce484222325
FNV64_PRIME = 0x100000001b3
MASK64 = 0xFFFFFFFFFFFFFFFF


def fnv1a64(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    h = FNV64_OFFSET
    for b in data:
        h ^= b
        h = (h * FNV64_PRIME) & MASK64
    return h


def canonical(op):
    """canonical string form of an op (single line, no ambiguity)"""
    return str(op).replace("\n", "\\n")


class ReceiptChain:
    """Append-only chain: receipt_i = fnv1a64(prev || op). Position is an
    integer index — never a time. genesis=None starts from the FNV offset
    basis (the empty-string hash)."""

    def __init__(self, genesis=None):
        self.head = genesis if genesis is not None else "%016x" % FNV64_OFFSET
        self.position = 0
        self.ops = []

    def append(self, op):
        r = "%016x" % fnv1a64(self.head + "|" + canonical(op))
        self.ops.append((self.position, canonical(op), r))
        self.head = r
        self.position += 1
        return r

    def verify(self):
        """recompute every link from genesis; True iff the chain is intact."""
        h = "%016x" % FNV64_OFFSET if self.genesis_basis else self.genesis_start
        for pos, op, r in self.ops:
            want = "%016x" % fnv1a64(h + "|" + op)
            if want != r:
                return False
            h = r
        return True

    @property
    def genesis_basis(self):
        return self._genesis is None

    @property
    def genesis_start(self):
        return self._genesis

    # store genesis privately so verify() can distinguish basis vs anchored
    def __init__(self, genesis=None):  # noqa: F811
        self._genesis = genesis
        self.head = genesis if genesis is not None else "%016x" % FNV64_OFFSET
        self.position = 0
        self.ops = []
