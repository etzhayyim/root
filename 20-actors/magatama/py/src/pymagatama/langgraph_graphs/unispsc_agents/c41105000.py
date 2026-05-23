from typing import TypedDict
from langgraph.graph import StateGraph, END
class SieveState(TypedDict):
    specs: dict
    approved: bool
def validate_mesh_specs(state: SieveState):
    state['approved'] = 'mesh_size' in state['specs'] and state['specs']['mesh_size'] > 0
    return state
graph = StateGraph(SieveState)
graph.add_node('validate', validate_mesh_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
