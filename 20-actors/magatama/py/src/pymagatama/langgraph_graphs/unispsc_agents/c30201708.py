from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AuditState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_acoustic_specs(state: AuditState):
    if state['specs'].get('db_rating', 0) < 30:
        state['validation_errors'].append('Acoustic rating insufficient')
    return state

def check_fire_safety(state: AuditState):
    if not state['specs'].get('fire_code_certified', False):
        state['validation_errors'].append('Fire safety certification missing')
    return state

graph = StateGraph(AuditState)
graph.add_node('acoustic_check', validate_acoustic_specs)
graph.add_node('fire_check', check_fire_safety)
graph.set_entry_point('acoustic_check')
graph.add_edge('acoustic_check', 'fire_check')
graph.add_edge('fire_check', END)
graph = graph.compile()