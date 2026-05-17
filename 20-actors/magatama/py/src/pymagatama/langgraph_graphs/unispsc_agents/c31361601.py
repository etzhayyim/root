from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AssemblyState(TypedDict):
    part_id: str
    weld_integrity_score: float
    compliance_docs: List[str]
    approved: bool

def validate_weld_integrity(state: AssemblyState):
    state['approved'] = state['weld_integrity_score'] > 0.95
    return state

def check_compliance(state: AssemblyState):
    state['approved'] = state['approved'] and len(state['compliance_docs']) >= 3
    return state

graph = StateGraph(AssemblyState)
graph.add_node('validate_weld', validate_weld_integrity)
graph.add_node('check_docs', check_compliance)
graph.set_entry_point('validate_weld')
graph.add_edge('validate_weld', 'check_docs')
graph.add_edge('check_docs', END)
graph = graph.compile()