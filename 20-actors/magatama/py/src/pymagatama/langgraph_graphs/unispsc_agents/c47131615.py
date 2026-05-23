from typing import TypedDict
from langgraph.graph import StateGraph, END

class BroomState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: BroomState):
    required = ['bristle_material', 'width_mm']
    all_present = all(k in state['specs'] for k in required)
    return {'approved': all_present}

def route_by_validation(state: BroomState):
    return 'approved' if state['approved'] else END

graph = StateGraph(BroomState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'approved': END})
graph.add_edge('validate', END)

app = graph.compile()
