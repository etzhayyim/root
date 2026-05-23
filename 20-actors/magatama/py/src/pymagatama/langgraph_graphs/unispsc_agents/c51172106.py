from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    material_name: str
    purity_level: float
    compliance_docs: List[str]
    validation_passed: bool

def validate_purity(state: PharmaState):
    passed = state['purity_level'] >= 99.0
    return {'validation_passed': passed}

def check_compliance(state: PharmaState):
    required = ['COA', 'MSDS', 'ISO_Cert']
    all_present = all(doc in state['compliance_docs'] for doc in required)
    return {'validation_passed': state['validation_passed'] and all_present}

graph = StateGraph(PharmaState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
