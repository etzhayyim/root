from typing import TypedDict
from langgraph.graph import StateGraph, END

class SkateSpecState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_safety_standards(state: SkateSpecState):
    standards = state['spec_data'].get('safety_certification_standards', '')
    return {'is_compliant': 'EN13843' in standards or 'ASTM' in standards}

graph = StateGraph(SkateSpecState)
graph.add_node('validate', validate_safety_standards)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()