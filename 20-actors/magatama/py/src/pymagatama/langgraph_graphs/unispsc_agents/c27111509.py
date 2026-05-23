from typing import TypedDict
from langgraph.graph import StateGraph, END

class AugerState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: AugerState):
    required = ['diameter', 'material', 'safety_rating']
    state['validation_passed'] = all(k in state['spec_data'] for k in required)
    return state

def check_compliance(state: AugerState):
    print(f"Validation result: {state['validation_passed']}")
    return state

graph = StateGraph(AugerState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
