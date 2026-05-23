from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    lot: str
    temp_log: list
    valid: bool

def validate_cold_chain(state: ReagentState):
    state['valid'] = all(t < 8.0 for t in state['temp_log'])
    print('Cold chain validation complete')
    return 'check_lot'

def check_lot_expiration(state: ReagentState):
    print('Checking lot registration')
    return END

graph = StateGraph(ReagentState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('check_lot', check_lot_expiration)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_lot')
graph.add_edge('check_lot', END)
app = graph.compile()
