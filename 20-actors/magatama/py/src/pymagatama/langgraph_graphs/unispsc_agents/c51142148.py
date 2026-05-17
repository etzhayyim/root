from typing import TypedDict
from langgraph.graph import StateGraph, END

class SodiumHyaluronateState(TypedDict):
    purity_pct: float
    sterility_report: str
    is_compliant: bool

def validate_purity(state: SodiumHyaluronateState):
    state['is_compliant'] = state['purity_pct'] >= 99.0
    return state

def check_sterility(state: SodiumHyaluronateState):
    if 'valid' not in state['sterility_report'].lower():
        state['is_compliant'] = False
    return state

graph = StateGraph(SodiumHyaluronateState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_sterility', check_sterility)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_sterility')
graph.add_edge('check_sterility', END)
app = graph.compile()