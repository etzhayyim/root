from typing import TypedDict
from langgraph.graph import StateGraph

class ProcurementState(TypedDict):
    purity: float
    has_gmp: bool
    is_approved: bool

def validate_compliance(state: ProcurementState):
    assert state['purity'] >= 99.0, 'Purity too low'
    assert state['has_gmp'], 'GMP required'
    return {'is_approved': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.set_finish_point('validate')
graph = graph.compile()
