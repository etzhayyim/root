from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HempRopeState(TypedDict):
    diameter_mm: float
    tensile_strength_kn: float
    inspection_result: bool

def validate_specs(state: HempRopeState):
    if state['diameter_mm'] > 0 and state['tensile_strength_kn'] > 0:
        return {'inspection_result': True}
    return {'inspection_result': False}

graph = StateGraph(HempRopeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()