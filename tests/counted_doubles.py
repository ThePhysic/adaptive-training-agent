"""Protocol recorder only: financial correctness is tested separately in PostgreSQL."""

from future_training.persistence.spending import LedgerFault
from future_training.providers.accounting import cost_micro


class RecorderLedger:
    def __init__(self):
        self.operations = []
        self.pairs = []
        self.tickets = set()
        self.disabled = False

    def invalidate(self, pair):
        self.tickets.discard(pair.pair)

    async def reserve_pair(self, pair):
        pair.checked()
        self.pairs.append(pair)
        self.operations.append(("reserve", pair.ordinal))

    async def claim(self, pair, kind):
        if self.disabled:
            raise LedgerFault("spending_disabled")
        if kind == "generation":
            if pair.pair not in self.tickets:
                raise LedgerFault("count_ticket_missing")
            self.tickets.remove(pair.pair)
        self.operations.append((kind, pair.ordinal))

    async def accept_count(self, pair, number):
        self.tickets.add(pair.pair)
        self.operations.append(("accept", number))

    async def settle_generation(self, pair, usage, **kwargs):
        self.operations.append(("settle", usage.input_tokens))
        return cost_micro(usage)

    async def abandon_pair(self, pair):
        self.invalidate(pair)
        self.operations.append(("abandon", pair.ordinal))
