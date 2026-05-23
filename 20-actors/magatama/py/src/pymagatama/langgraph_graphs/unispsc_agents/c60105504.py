from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LandscapeMaterialState(TypedDict):
    material_type: str
    validation_status: bool
    compliance_tags: List[str]

def validate_format(state: LandscapeMaterialState):
    state['validation_status'] = state['material_type'] in ['digital', 'physical']
    return state

def check_compliance(state: LandscapeMaterialState):
    state['compliance_tags'] = ['intellectual_property_cleared']
    return state

graph = StateGraph(LandscapeMaterialState)
graph.add_node('validate', validate_format)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

compiled_graph = graph.compile()
