from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AdhesionState(TypedDict):
    material_code: str
    viscosity_ok: bool
    safety_check_passed: bool
    log: List[str]

def validate_viscosity(state: AdhesionState):
    # Simulate CAD/Spec validation logic
    state['viscosity_ok'] = True
    state['log'].append('Viscosity validated against industry specs.')
    return state

def run_safety_protocol(state: AdhesionState):
    # Simulate handling dangerous goods
    state['safety_check_passed'] = True
    state['log'].append('Chemical safety classification passed.')
    return state

builder = StateGraph(AdhesionState)
builder.add_node('validate', validate_viscosity)
builder.add_node('safety', run_safety_protocol)
builder.set_entry_point('validate')
builder.add_edge('validate', 'safety')
builder.add_edge('safety', END)
graph = builder.compile()
