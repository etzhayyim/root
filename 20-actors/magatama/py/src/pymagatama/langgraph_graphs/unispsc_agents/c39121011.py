from typing import TypedDict
from langgraph.graph import StateGraph, END

class UPSState(TypedDict):
    capacity_va: int
    target_load: float
    validation_passed: bool

def validate_specs(state: UPSState):
    if state['capacity_va'] * 0.8 < state['target_load']:
        print('Warning: Capacity insufficient for load.')
        return {'validation_passed': False}
    return {'validation_passed': True}

graph = StateGraph(UPSState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()