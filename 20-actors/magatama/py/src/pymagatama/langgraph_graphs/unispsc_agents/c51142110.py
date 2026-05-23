from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    batch_number: str
    purity_level: float
    compliance_docs: bool
    approved: bool

def validate_purity(state: PharmaState):
    state['approved'] = state['purity_level'] >= 99.0
    return 'validate_purity_check'

def check_compliance(state: PharmaState):
    state['approved'] = state['approved'] and state['compliance_docs']
    return 'compliance_check'

graph = StateGraph(PharmaState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

graph.compile()
