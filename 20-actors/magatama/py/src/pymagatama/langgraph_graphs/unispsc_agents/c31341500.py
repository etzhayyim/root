from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    material_type: str
    solvent_grade: str
    is_verified: bool

def validate_solvent_compatibility(state: AssemblyState):
    # logic to check if solvent matches sheet chemistry
    state['is_verified'] = True
    return 'verified'

def finalize_order(state: AssemblyState):
    return 'complete'

graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_solvent_compatibility)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
compiled_graph = graph.compile()
