from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AuditState(TypedDict):
    item_name: str
    specs: dict
    is_compliant: bool

def validate_specs(state: AuditState):
    required_keys = ['Dimensions', 'Impact-Resistance-Rating']
    state['is_compliant'] = all(k in state['specs'] for k in required_keys)
    return state

def check_dimensions(state: AuditState):
    if 'Dimensions' in state['specs'] and not state['specs']['Dimensions']:
        state['is_compliant'] = False
    return state

graph = StateGraph(AuditState)
graph.add_node("validate", validate_specs)
graph.add_node("dimension_check", check_dimensions)
graph.set_entry_point("validate")
graph.add_edge("validate", "dimension_check")
graph.add_edge("dimension_check", END)
graph = graph.compile()
