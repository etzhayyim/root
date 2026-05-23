from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    api_name: str
    purity_level: float
    compliance_docs: List[str]
    approved: bool

def validate_purity(state: ProcurementState):
    is_pure = state['purity_level'] >= 99.0
    return {'approved': is_pure}

def check_compliance(state: ProcurementState):
    required = ['CoA', 'GMP_Cert']
    has_all = all(item in state['compliance_docs'] for item in required)
    return {'approved': state['approved'] and has_all}

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
