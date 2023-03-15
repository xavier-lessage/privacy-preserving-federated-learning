from PROJH402.src.Block import State
from PROJH402.src.Transaction import Transaction

t = Transaction("A", "B", {"action": "add_k", "input": 3}, 0)
s = State()
s.apply_transaction(t)
print(s.n)