from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NameplateState(TypedDict):
    material: str
    specs: dict
    approved: bool

def validate_material(state: NameplateState) -> NameplateState:
    if state['material'] in ['Acrylic', 'Polycarbonate', 'PVC']:
        state['approved'] = True
    return state

def check_compliance(state: NameplateState) -> NameplateState:
    if state['approved']:
        state['approved'] = 'UL_Certified' in state['specs']
    return state

graph = StateGraph(NameplateState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
