from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    compliance_docs: List[str]
    approved: bool

def validate_purity(state: ProcurementState):
    state['approved'] = state['purity_level'] >= 99.0
    return 'purity_ready'

def check_compliance(state: ProcurementState):
    state['approved'] = state['approved'] and len(state['compliance_docs']) >= 3
    return 'compliance_ready'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
