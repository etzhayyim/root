from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtruderState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: ExtruderState):
    # Business logic for extrusion equipment validation
    pressure = state['spec_data'].get('pressure', 0)
    state['validation_passed'] = pressure > 0
    return state

graph = StateGraph(ExtruderState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()