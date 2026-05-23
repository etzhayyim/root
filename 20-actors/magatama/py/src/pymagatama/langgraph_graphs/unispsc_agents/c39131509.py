from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class MarkerState(TypedDict):
    part_number: str
    material_spec: str
    compliant: bool

def validate_material(state: MarkerState) -> MarkerState:
    # Logic to verify material temperature rating against spec
    state['compliant'] = 'heat-resistant' in state['material_spec'].lower()
    return state

def route_by_compliance(state: MarkerState) -> str:
    return 'process' if state['compliant'] else END

graph = StateGraph(MarkerState)
graph.add_node('validate', validate_material)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
