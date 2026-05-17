from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CanvasState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    approved: bool

def validate_canvas_quality(state: CanvasState):
    errors = []
    if state['specifications'].get('canvas_weight_gsm', 0) < 200:
        errors.append('Canvas weight below professional threshold')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(CanvasState)
graph.add_node('validate', validate_canvas_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()