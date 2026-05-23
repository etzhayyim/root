from typing import TypedDict
from langgraph.graph import StateGraph, END

class BerylliumCastingState(TypedDict):
    spec_data: dict
    validated: bool
    safety_clearance: bool

def validate_materials(state: BerylliumCastingState):
    content = state['spec_data'].get('be_content', 0)
    state['validated'] = content > 0
    return state

def check_safety_protocols(state: BerylliumCastingState):
    state['safety_clearance'] = state['spec_data'].get('safety_cert', False)
    return state

graph = StateGraph(BerylliumCastingState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('safety_check', check_safety_protocols)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'safety_check')
graph.add_edge('safety_check', END)
app = graph.compile()
