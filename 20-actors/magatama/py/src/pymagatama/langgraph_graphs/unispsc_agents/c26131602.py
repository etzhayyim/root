from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StopLogState(TypedDict):
    material_spec: str
    pressure_rating: float
    inspection_passed: bool
graph = StateGraph(StopLogState)
def validate_structural_integrity(state: StopLogState):
    return {'inspection_passed': state['pressure_rating'] > 500}
graph.add_node('validation', validate_structural_integrity)
graph.add_edge('validation', END)
graph.set_entry_point('validation')
graph = graph.compile()