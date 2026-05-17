from typing import TypedDict
from langgraph.graph import StateGraph, END

class PressState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_safety_specs(state: PressState):
    required = ['tonnage_capacity', 'safety_interlock_system']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def route_by_safety(state: PressState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(PressState)
graph.add_node('validate', validate_safety_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_safety)
graph.add_edge('process', END)
graph = graph.compile()