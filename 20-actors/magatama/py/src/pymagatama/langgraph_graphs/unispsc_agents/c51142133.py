from typing import TypedDict
from langgraph.graph import StateGraph, END

class BromfenacState(TypedDict):
    purity: float
    gmp_certified: bool
    validation_status: str

def validate_purity(state: BromfenacState):
    state['validation_status'] = 'Pass' if state['purity'] >= 99.0 else 'Fail'
    return state

def check_compliance(state: BromfenacState):
    if not state['gmp_certified']:
        state['validation_status'] = 'Reject_Regulatory'
    return state

graph = StateGraph(BromfenacState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()