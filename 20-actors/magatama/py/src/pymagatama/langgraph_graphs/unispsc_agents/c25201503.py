from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftComponentState(TypedDict):
    part_number: str
    compliance_docs: list
    is_airworthy: bool

def validate_specs(state: AircraftComponentState):
    state['is_airworthy'] = len(state['compliance_docs']) > 2
    return state

def audit_log(state: AircraftComponentState):
    print(f'Auditing component: {state['part_number']}')
    return state

builder = StateGraph(AircraftComponentState)
builder.add_node('validate', validate_specs)
builder.add_node('audit', audit_log)
builder.add_edge('validate', 'audit')
builder.add_edge('audit', END)
builder.set_entry_point('validate')
graph = builder.compile()