from typing import TypedDict
from langgraph.graph import StateGraph, END

class BearingPadState(TypedDict):
    load_capacity: float
    material_spec: str
    validation_status: bool

def validate_load_capacity(state: BearingPadState):
    if state['load_capacity'] > 0:
        return {'validation_status': True}
    return {'validation_status': False}

def finalize_spec(state: BearingPadState):
    print('Finalizing procurement specs for bearing pads')
    return {}

graph = StateGraph(BearingPadState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('finalize', finalize_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()