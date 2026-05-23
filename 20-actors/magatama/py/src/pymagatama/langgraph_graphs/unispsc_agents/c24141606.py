from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    material_type: str
    density_kg_m3: float
    pass_inspection: bool

def validate_density(state: PackagingState):
    state['pass_inspection'] = state['density_kg_m3'] > 0.5
    return state

def packing_workflow():
    graph = StateGraph(PackagingState)
    graph.add_node('density_check', validate_density)
    graph.set_entry_point('density_check')
    graph.add_edge('density_check', END)
    return graph.compile()

graph = packing_workflow()
