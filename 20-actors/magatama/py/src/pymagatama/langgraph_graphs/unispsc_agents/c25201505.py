from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftComponentState(TypedDict):
    part_id: str
    compliance_docs: list[str]
    validation_status: bool

def validate_components(state: AircraftComponentState):
    required = {'AS9100', 'MaterialCert', 'NDT'}
    state['validation_status'] = required.issubset(set(state['compliance_docs']))
    return state

builder = StateGraph(AircraftComponentState)
builder.add_node('validate', validate_components)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()
