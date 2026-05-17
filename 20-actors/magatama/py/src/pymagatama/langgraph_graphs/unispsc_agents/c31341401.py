from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    part_number: str
    weld_strength: float
    inspection_passed: bool
    compliance_tags: List[str]

def validate_weld_integrity(state: AssemblyState) -> AssemblyState:
    # Rule: Weld strength must exceed 200MPa for aerospace compliance
    state['inspection_passed'] = state['weld_strength'] >= 200.0
    return state

def check_export_compliance(state: AssemblyState) -> AssemblyState:
    # Example logic for dual-use tracking
    state['compliance_tags'] = ['Export-Control-Check-Required'] if state['inspection_passed'] else []
    return state

graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_weld_integrity)
graph.add_node('compliance', check_export_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()