from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    gmp_compliant: bool
    validation_status: str

def check_purity(state: ProcurementState):
    state['validation_status'] = 'Pass' if state['purity'] >= 99.0 else 'Fail'
    return state

def check_compliance(state: ProcurementState):
    if not state.get('gmp_compliant'):
        state['validation_status'] = 'Fail'
    return state

graph = StateGraph(ProcurementState)
graph.add_node('purity_check', check_purity)
graph.add_node('gmp_check', check_compliance)
graph.add_edge('purity_check', 'gmp_check')
graph.add_edge('gmp_check', END)
graph.set_entry_point('purity_check')
procurement_graph = graph.compile()