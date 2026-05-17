from typing import TypedDict
from langgraph.graph import StateGraph, END

class CleaningAgentState(TypedDict):
    chemical_data: dict
    compliance_ok: bool
    approval_status: str

def validate_safety_specs(state: CleaningAgentState) -> CleaningAgentState:
    ph = state['chemical_data'].get('ph_level', 7)
    state['compliance_ok'] = 2 <= ph <= 12
    return state

def finalize_procurement(state: CleaningAgentState) -> CleaningAgentState:
    state['approval_status'] = 'APPROVED' if state['compliance_ok'] else 'REJECTED'
    return state

graph = StateGraph(CleaningAgentState)
graph.add_node('validate', validate_safety_specs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')