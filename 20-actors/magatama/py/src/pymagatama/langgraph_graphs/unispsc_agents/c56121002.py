from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    specs: dict
    approved: bool

def validate_specs(state: ProcurementState):
    required_keys = ['material', 'dimensions', 'fire_rating']
    state['approved'] = all(k in state['specs'] for k in required_keys)
    return {'approved': state['approved']}

def route_by_approval(state: ProcurementState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()