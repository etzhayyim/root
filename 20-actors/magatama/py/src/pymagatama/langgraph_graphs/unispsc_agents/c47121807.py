from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PlumbingToolState(TypedDict):
    item_name: str
    specs: dict
    is_approved: bool

def validate_specs(state: PlumbingToolState):
    required = ['diameter', 'material']
    all_present = all(k in state['specs'] for k in required)
    return {'is_approved': all_present}

def route_by_validation(state: PlumbingToolState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(PlumbingToolState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()