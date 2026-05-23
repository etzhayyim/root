from typing import TypedDict
from langgraph.graph import StateGraph, END

class CouplingState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: CouplingState):
    required = ['torque_capacity_nm', 'input_speed_rpm']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def route_by_validation(state: CouplingState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(CouplingState)
graph.add_node('process', validate_specs)
graph.set_entry_point('process')
graph.add_conditional_edges('process', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()
