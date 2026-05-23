from typing import TypedDict
from langgraph.graph import StateGraph, END

class StorageState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: StorageState):
    required_keys = ['load_capacity_rating', 'dimensions_mm']
    state['approved'] = all(k in state['specs'] for k in required_keys)
    return state

def route_by_approval(state: StorageState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(StorageState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_approval, {'approved': END, 'rejected': END})
app = graph.compile()
