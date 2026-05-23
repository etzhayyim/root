from typing import TypedDict
from langgraph.graph import StateGraph, END

class MedicalTextileState(TypedDict):
    material: str
    sterilization_confirmed: bool
    compliance_score: float

def validate_material(state: MedicalTextileState):
    state['compliance_score'] = 1.0 if state['material'] == 'polyester-blend' else 0.5
    return state

def check_sterilization(state: MedicalTextileState):
    state['sterilization_confirmed'] = True
    return state

graph = StateGraph(MedicalTextileState)
graph.add_node('validate', validate_material)
graph.add_node('sterilize', check_sterilization)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sterilize')
graph.add_edge('sterilize', END)
graph = graph.compile()
