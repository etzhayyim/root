from typing import TypedDict
from langgraph.graph import StateGraph, END

class GarmentState(TypedDict):
    material: str
    compliance_cert: bool
    inspection_passed: bool

def validate_materials(state: GarmentState):
    state['compliance_cert'] = state['material'] in ['cotton', 'polyester-blend']
    return state

def run_inspection(state: GarmentState):
    state['inspection_passed'] = state['compliance_cert']
    return state

graph = StateGraph(GarmentState)
graph.add_node('validate', validate_materials)
graph.add_node('inspect', run_inspection)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
app = graph.compile()