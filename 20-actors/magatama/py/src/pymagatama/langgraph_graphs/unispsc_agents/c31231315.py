from langgraph.graph import StateGraph, END
from typing import TypedDict

class GlassTubeState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_dimensions(state: GlassTubeState):
    od = state['spec_data'].get('od', 0)
    thickness = state['spec_data'].get('thickness', 0)
    state['validation_passed'] = od > 0 and thickness > 0
    return state

def assess_fragility(state: GlassTubeState):
    print('Assessing packing requirements for glass tube shipment.')
    return state

graph = StateGraph(GlassTubeState)
graph.add_node('validate', validate_dimensions)
graph.add_node('fragility', assess_fragility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'fragility')
graph.add_edge('fragility', END)
app = graph.compile()