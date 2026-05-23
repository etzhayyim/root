from typing import TypedDict
from langgraph.graph import StateGraph, END

class AbrasiveProcessState(TypedDict):
    spec_data: dict
    validation_passed: bool
    safety_check: bool

def validate_specs(state: AbrasiveProcessState) -> AbrasiveProcessState:
    # Logic to check grit compatibility with backing material
    state['validation_passed'] = 'grit_size' in state['spec_data']
    return state

def safety_compliance(state: AbrasiveProcessState) -> AbrasiveProcessState:
    # Logic to verify ISO/ANSI safety standards for grinding products
    state['safety_check'] = True
    return state

graph = StateGraph(AbrasiveProcessState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
