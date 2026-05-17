from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_certification(state: AircraftState):
    cert = state['specs'].get('airworthiness')
    return {'validation_passed': cert is not None}

def route_by_validation(state: AircraftState):
    return 'valid' if state['validation_passed'] else END

graph = StateGraph(AircraftState)
graph.add_node('cert_check', validate_certification)
graph.add_edge('cert_check', END)
graph.set_entry_point('cert_check')
graph = graph.compile()