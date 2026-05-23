from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WireManagementState(TypedDict):
    item_id: str
    specs: dict
    approved: bool

def validate_materials(state: WireManagementState):
    # Simulate material compliance check
    is_compliant = state['specs'].get('flame_retardancy', False) == 'V-0'
    return {'approved': is_compliant}

def route_by_spec(state: WireManagementState):
    return 'process' if state['approved'] else 'reject'

graph = StateGraph(WireManagementState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
