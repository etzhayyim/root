from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class LabCoolingState(TypedDict):
    part_id: str
    compatibility_verified: bool
    thermal_rating: float

def check_compatibility(state: LabCoolingState):
    state['compatibility_verified'] = True
    return 'compatibility_verified'

def inspect_specifications(state: LabCoolingState):
    return 'spec_inspected'

graph = StateGraph(LabCoolingState)
graph.add_node('compatibility_check', check_compatibility)
graph.add_node('spec_validation', inspect_specifications)
graph.set_entry_point('compatibility_check')
graph.add_edge('compatibility_check', 'spec_validation')
graph.add_edge('spec_validation', END)
graph = graph.compile()