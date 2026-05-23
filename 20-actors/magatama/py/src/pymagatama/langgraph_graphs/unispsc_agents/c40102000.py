from typing import TypedDict
from langgraph.graph import StateGraph, END

class BoilerState(TypedDict):
    pressure_rating: float
    safety_certs: list
    emission_ok: bool

def validate_pressure(state: BoilerState):
    print(f"Validating pressure: {state['pressure_rating']}")
    return {'safety_certs': state.get('safety_certs', []) + ['ASME_VAL']}

def check_compliance(state: BoilerState):
    return {'emission_ok': True}

graph = StateGraph(BoilerState)
graph.add_node("validate_pressure", validate_pressure)
graph.add_node("compliance_check", check_compliance)
graph.set_entry_point("validate_pressure")
graph.add_edge("validate_pressure", "compliance_check")
graph.add_edge("compliance_check", END)
compiled_graph = graph.compile()
