from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    material_name: str
    purity_level: float
    compliance_docs: List[str]
    is_approved: bool

def validate_purity(state: PharmState):
    state['is_approved'] = state['purity_level'] >= 99.0
    return state

def check_compliance(state: PharmState):
    required = {'GMP', 'COA', 'MSDS'}
    state['is_approved'] = state['is_approved'] and required.issubset(set(state['compliance_docs']))
    return state

graph = StateGraph(PharmState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
