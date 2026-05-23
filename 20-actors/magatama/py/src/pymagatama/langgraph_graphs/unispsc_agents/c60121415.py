from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FrameKitState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: FrameKitState):
    required = ['material', 'dimensions', 'finish']
    errors = [f'Missing {f}' for f in required if f not in state['specs']]
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(FrameKitState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
