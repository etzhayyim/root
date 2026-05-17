from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    drug_name: str
    purity_level: float
    compliance_docs: List[str]
    approved: bool

def validate_purity(state: ProcurementState):
    is_pure = state['purity_level'] >= 99.0
    return {'approved': is_pure}

def check_compliance(state: ProcurementState):
    required = {'GMP', 'COA'}
    is_compliant = required.issubset(set(state['compliance_docs']))
    return {'approved': state['approved'] and is_compliant}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()