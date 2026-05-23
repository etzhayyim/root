from typing import TypedDict
from langgraph.graph import StateGraph, END

class MountingSpecState(TypedDict):
    material: str
    pull_force_newtons: float
    compliance_certified: bool

def validate_material(state: MountingSpecState):
    assert state['material'] in ['Stainless Steel', 'Polymer', 'Galvanized Steel']
    return {"material": state['material']}

def check_load_capacity(state: MountingSpecState):
    return {"compliance_certified": state['pull_force_newtons'] > 500}

graph = StateGraph(MountingSpecState)
graph.add_node("validate", validate_material)
graph.add_node("capacity", check_load_capacity)
graph.set_entry_point("validate")
graph.add_edge("validate", "capacity")
graph.add_edge("capacity", END)
graph = graph.compile()
