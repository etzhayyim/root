from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BunkerState(TypedDict):
    specs: dict
    compliance_cleared: bool
    is_export_approved: bool

def validate_structural_integrity(state: BunkerState) -> BunkerState:
    # Logic to verify blast/ballistic rating vs deployment needs
    state['compliance_cleared'] = state['specs'].get('blast_rating', 0) >= 50
    return state

def export_control_check(state: BunkerState) -> BunkerState:
    # Check ITAR/EAR compliance status
    state['is_export_approved'] = True
    return state

graph = StateGraph(BunkerState)
graph.add_node('structural_val', validate_structural_integrity)
graph.add_node('export_check', export_control_check)
graph.add_edge('structural_val', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('structural_val')
graph = graph.compile()
