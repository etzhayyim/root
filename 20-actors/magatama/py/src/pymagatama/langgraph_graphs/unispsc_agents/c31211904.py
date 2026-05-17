from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrushSpecState(TypedDict):
    material: str
    width_mm: int
    is_solvent_resistant: bool
    validation_passed: bool

def validate_specs(state: BrushSpecState):
    state['validation_passed'] = bool(state['material'] and state['width_mm'] > 0)
    return state

def check_compliance(state: BrushSpecState):
    if state.get('is_solvent_resistant', False):
        print('Validated for industrial use')
    return {'validation_passed': True}

graph = StateGraph(BrushSpecState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()