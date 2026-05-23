from typing import TypedDict
from langgraph.graph import StateGraph, END

class OphthalmicSpecState(TypedDict):
    material: str
    sterilization_validated: bool
    compliance_docs: list
    approved: bool

def validate_materials(state: OphthalmicSpecState):
    state['approved'] = state['material'] == 'MedicalGradeStainless' and state['sterilization_validated']
    return state

builder = StateGraph(OphthalmicSpecState)
builder.add_node('validate', validate_materials)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
