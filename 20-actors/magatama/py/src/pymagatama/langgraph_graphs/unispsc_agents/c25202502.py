from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftLightingState(TypedDict):
    part_number: str
    certification_docs: list[str]
    compliance_status: bool

def validate_specs(state: AircraftLightingState):
    # Simulate FAA and DO-160 environmental spec validation logic
    state['compliance_status'] = len(state['certification_docs']) > 0
    return state

def approval_check(state: AircraftLightingState):
    return 'APPROVED' if state['compliance_status'] else 'REJECTED'

graph = StateGraph(AircraftLightingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)