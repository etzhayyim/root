from typing import TypedDict
from langgraph.graph import StateGraph, END

class MeshProcessState(TypedDict):
    material_type: str
    mesh_size: float
    inspection_passed: bool

def validate_mesh_specs(state: MeshProcessState):
    state['inspection_passed'] = state['mesh_size'] > 0 and state['material_type'] != "-"
    return state

def route_verification(state: MeshProcessState):
    return "verified" if state['inspection_passed'] else END

graph = StateGraph(MeshProcessState)
graph.add_node("validate", validate_mesh_specs)
graph.add_edge("validate", END)
graph.set_entry_point("validate")
graph = graph.compile()