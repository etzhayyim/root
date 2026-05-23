from typing import TypedDict
from langgraph.graph import StateGraph, END

class SlipperSpecState(TypedDict):
    material: str
    safety_check: bool
    approved: bool

def validate_materials(state: SlipperSpecState):
    state['safety_check'] = 'non-toxic' in state['material'].lower()
    return state

def check_compliance(state: SlipperSpecState):
    state['approved'] = state['safety_check']
    return state

graph = StateGraph(SlipperSpecState)
graph.add_node('material_validation', validate_materials)
graph.add_node('compliance_review', check_compliance)
graph.add_edge('material_validation', 'compliance_review')
graph.add_edge('compliance_review', END)
graph.set_entry_point('material_validation')
compiled_graph = graph.compile()
