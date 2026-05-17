from typing import TypedDict
from langgraph.graph import StateGraph, END

class PellicleState(TypedDict):
    specs: dict
    validation_status: bool
    error_log: list

def validate_specs(state: PellicleState):
    required = ['transmittance_rate', 'thermal_stability']
    valid = all(k in state['specs'] for k in required)
    return {'validation_status': valid, 'error_log': [] if valid else ['Missing technical parameters']}

def route_verification(state: PellicleState):
    return 'validate' if state['validation_status'] else END

graph = StateGraph(PellicleState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()