from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastState(TypedDict):
    part_id: str
    material_spec: str
    tolerance_passed: bool
    approved: bool

def validate_material(state: CastState) -> CastState:
    # Logic to verify casting material composition
    state['material_spec'] = 'Verified' if state['material_spec'] else 'Missing'
    return state

def validate_tolerance(state: CastState) -> CastState:
    # Logic to verify dimension measurements
    state['tolerance_passed'] = True
    return state

graph = StateGraph(CastState)
graph.add_node('MaterialCheck', validate_material)
graph.add_node('ToleranceCheck', validate_tolerance)
graph.set_entry_point('MaterialCheck')
graph.add_edge('MaterialCheck', 'ToleranceCheck')
graph.add_edge('ToleranceCheck', END)
app = graph.compile()