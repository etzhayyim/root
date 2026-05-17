from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    raw_data: dict
    validated: bool
    compliance_score: float

def validate_extract(state: ProcurementState):
    data = state.get('raw_data', {})
    score = 1.0 if 'purity' in data and data['purity'] > 0.9 else 0.5
    return {'validated': True, 'compliance_score': score}

def check_compliance(state: ProcurementState):
    return 'compliant' if state['compliance_score'] > 0.8 else 'flag_for_review'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_extract)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.set_entry_point('validate')
graph.add_edge('compliance', END)
graph = graph.compile()