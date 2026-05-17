from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OvershoeState(TypedDict):
    material_type: str
    iso_rating: str
    compliance_ok: bool

def validate_materials(state: OvershoeState):
    state['compliance_ok'] = state['material_type'] in ['Latex', 'PE', 'CPE']
    return state

def check_iso_standards(state: OvershoeState):
    if state['compliance_ok']:
        state['compliance_ok'] = 'ISO' in state['iso_rating']
    return state

graph = StateGraph(OvershoeState)
graph.add_node('material_check', validate_materials)
graph.add_node('iso_check', check_iso_standards)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'iso_check')
graph.add_edge('iso_check', END)
graph = graph.compile()