from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftState(TypedDict):
    part_number: str
    material_certs: bool
    faa_approval: bool
    is_airworthy: bool

def validate_structural_spec(state: AircraftState):
    state['is_airworthy'] = state['material_certs'] and state['faa_approval']
    return state

workflow = StateGraph(AircraftState)
workflow.add_node('validate_spec', validate_structural_spec)
workflow.set_entry_point('validate_spec')
workflow.add_edge('validate_spec', END)
graph = workflow.compile()
