from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    cas: str
    is_compliant: bool

def validate_purity(state: ProcurementState):
    state['is_compliant'] = state['purity'] >= 99.0
    return state

def check_cas(state: ProcurementState):
    if state['cas'] != '62-33-9':
        state['is_compliant'] = False
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_cas', check_cas)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_cas')
graph.add_edge('check_cas', END)
app = graph.compile()
