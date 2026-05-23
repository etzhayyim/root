from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_docs: list
    status: str

def validate_purity(state: PharmaState):
    is_valid = state['purity_level'] >= 99.9
    return {'status': 'VALIDATED' if is_valid else 'REJECTED'}

def check_compliance(state: PharmaState):
    has_gmp = 'GMP' in state['compliance_docs']
    return {'status': 'COMPLIANT' if has_gmp else 'NON_COMPLIANT'}

graph = StateGraph(PharmaState)
graph.add_node('ValidatePurity', validate_purity)
graph.add_node('CheckCompliance', check_compliance)
graph.set_entry_point('ValidatePurity')
graph.add_edge('ValidatePurity', 'CheckCompliance')
graph.add_edge('CheckCompliance', END)
app = graph.compile()
