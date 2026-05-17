from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MachineState(TypedDict):
    machine_specs: dict
    validation_errors: List[str]
    approved: bool

def validate_safety_specs(state: MachineState) -> MachineState:
    specs = state.get('machine_specs', {})
    if 'safety_light_curtain' not in specs:
        state['validation_errors'].append('Missing mandatory safety light curtain spec')
    return state

def check_capacity(state: MachineState) -> MachineState:
    if state['machine_specs'].get('tonnage', 0) <= 0:
        state['validation_errors'].append('Invalied tonnage capacity')
    return state

builder = StateGraph(MachineState)
builder.add_node('safety_check', validate_safety_specs)
builder.add_node('capacity_check', check_capacity)
builder.set_entry_point('safety_check')
builder.add_edge('safety_check', 'capacity_check')
builder.add_edge('capacity_check', END)
graph = builder.compile()