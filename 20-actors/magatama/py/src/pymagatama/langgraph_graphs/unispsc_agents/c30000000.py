from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ConstructionState(TypedDict):
    materials: List[str]
    compliance_report: str
    is_approved: bool

def validate_specs(state: ConstructionState):
    state['is_approved'] = all(m != '' for m in state['materials'])
    return state

def check_compliance(state: ConstructionState):
    state['compliance_report'] = 'Standard compliance verified' if state['is_approved'] else 'Missing specs'
    return state

graph = StateGraph(ConstructionState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
