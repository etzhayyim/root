from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ElectricalBoxState(TypedDict):
    material: str
    ip_rating: str
    specs_verified: bool

def validate_material(state: ElectricalBoxState):
    state['specs_verified'] = state['material'] in ['Aluminum', 'Cast Iron']
    return state

def check_certification(state: ElectricalBoxState):
    print(f'Checking certification for IP rating: {state.get("ip_rating")}')
    return state

graph = StateGraph(ElectricalBoxState)
graph.add_node('validate', validate_material)
graph.add_node('certify', check_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
app = graph.compile()
