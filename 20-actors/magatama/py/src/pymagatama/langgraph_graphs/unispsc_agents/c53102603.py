from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PajamaSpecs(TypedDict):
    material: str
    size: str
    safety_certs: List[str]
    validated: bool

def validate_materials(state: PajamaSpecs):
    # Business logic for textile safety validation
    state['validated'] = all(['flame_resistant' in cert for cert in state['safety_certs']])
    return state

builder = StateGraph(PajamaSpecs)
builder.add_node('validate', validate_materials)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
