from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AdhesiveState(TypedDict):
    material_code: str
    viscosity: float
    is_verified: bool
    process_steps: List[str]

def validate_viscosity(state: AdhesiveState) -> AdhesiveState:
    # Specialized check for robotic dispensing tolerance
    state['is_verified'] = 500 <= state['viscosity'] <= 1500
    return state

def plan_dispensing(state: AdhesiveState) -> AdhesiveState:
    if state['is_verified']:
        state['process_steps'] = ['surface_prep', 'robotic_dispense', 'uv_cure', 'thermal_curing']
    else:
        state['process_steps'] = ['request_retest']
    return state

builder = StateGraph(AdhesiveState)
builder.add_node('validate', validate_viscosity)
builder.add_node('plan', plan_dispensing)
builder.set_entry_point('validate')
builder.add_edge('validate', 'plan')
builder.add_edge('plan', END)
graph = builder.compile()