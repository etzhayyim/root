from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalSpecState(TypedDict):
    material: str
    is_sterile: bool
    compliance_docs: list
    metadata: dict

def validate_material(state: SurgicalSpecState):
    state['metadata'] = {'valid': state['material'] == 'surgical-grade-steel'}
    return state

def check_sterilization(state: SurgicalSpecState):
    state['metadata']['sterilized'] = state['is_sterile']
    return state

graph = StateGraph(SurgicalSpecState)
graph.add_node('validate', validate_material)
graph.add_node('sterility_check', check_sterilization)
graph.add_edge('validate', 'sterility_check')
graph.add_edge('sterility_check', END)
graph.set_entry_point('validate')
app = graph.compile()