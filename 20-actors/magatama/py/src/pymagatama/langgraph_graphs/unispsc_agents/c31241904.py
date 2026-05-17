from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GlassDomeState(TypedDict):
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_dimensions(state: GlassDomeState):
    errs = []
    if state['specs'].get('diameter_mm', 0) <= 0:
        errs.append('Invalid Diameter')
    return {'validation_passed': len(errs) == 0, 'errors': errs}

def check_transparency(state: GlassDomeState):
    return {'validation_passed': state['validation_passed'] and state['specs'].get('transmission', 0) > 0.9}

builder = StateGraph(GlassDomeState)
builder.add_node('validate_dim', validate_dimensions)
builder.add_node('check_optics', check_transparency)
builder.add_edge('validate_dim', 'check_optics')
builder.add_edge('check_optics', END)
builder.set_entry_point('validate_dim')
graph = builder.compile()