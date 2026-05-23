from typing import TypedDict
from langgraph.graph import StateGraph, END

class AntacidState(TypedDict):
    batch_id: str
    ph_level: float
    has_pharmaceutical_cert: bool

def validate_quality(state: AntacidState):
    if state['ph_level'] < 8.0 or state['ph_level'] > 8.6:
        return {'status': 'REJECTED'}
    return {'status': 'APPROVED'}

def check_compliance(state: AntacidState):
    if not state.get('has_pharmaceutical_cert'):
        return {'status': 'COMPLIANCE_FAILURE'}
    return {'status': 'COMPLIANCE_PASSED'}

graph = StateGraph(AntacidState)
graph.add_node('validate', validate_quality)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph.compile()
