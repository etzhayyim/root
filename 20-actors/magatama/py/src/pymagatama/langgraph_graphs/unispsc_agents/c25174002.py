from typing import TypedDict
from langgraph.graph import StateGraph, END

class RadiatorState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: RadiatorState):
    required = ['pressure_rating', 'material']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

graph = StateGraph(RadiatorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile_graph = graph.compile()
