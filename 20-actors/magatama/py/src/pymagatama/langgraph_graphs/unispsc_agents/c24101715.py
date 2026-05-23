from typing import TypedDict
from langgraph.graph import StateGraph, END

class BeltState(TypedDict):
    material: str
    width_mm: float
    tensile_strength: float
    is_valid: bool

def validate_specs(state: BeltState):
    state['is_valid'] = state['width_mm'] > 0 and state['tensile_strength'] > 100
    return state

def check_compliance(state: BeltState):
    if state['is_valid']:
        print('Specifications verified.')
    return {'is_valid': state['is_valid']}

graph = StateGraph(BeltState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
