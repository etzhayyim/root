from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    compliance_docs: bool
    storage_temp_ok: bool

def validate_quality(state: ProcurementState):
    assert state['purity'] >= 99.0, 'Purity below pharmaceutical Grade'
    return {'status': 'validated'}

def check_compliance(state: ProcurementState):
    return {'compliant': state['compliance_docs'] and state['storage_temp_ok']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_quality)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
