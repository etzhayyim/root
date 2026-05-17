from typing import TypedDict
from langgraph.graph import StateGraph, END

class BoxingGearState(TypedDict):
    weight_oz: float
    material: str
    is_certified: bool

def validate_specs(state: BoxingGearState):
    if state['weight_oz'] < 8 or state['weight_oz'] > 20:
        raise ValueError('Invalid weight for boxing gloves.')
    return {'is_certified': True}

graph = StateGraph(BoxingGearState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()