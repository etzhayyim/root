from langgraph.graph import StateGraph, END
from typing import TypedDict

class TargetState(TypedDict):
    material: str
    specs_verified: bool

def validate_target_material(state: TargetState):
    return {'specs_verified': state['material'] in ['Polymer', 'Steel', 'Paper Board']}

def finalize_procurement(state: TargetState):
    return {'specs_verified': True}

graph = StateGraph(TargetState)
graph.add_node('validate', validate_target_material)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
# Graph defined and compiled
compiled_graph = graph.compile()