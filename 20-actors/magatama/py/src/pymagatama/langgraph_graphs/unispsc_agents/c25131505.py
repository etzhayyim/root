from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftState(TypedDict):
    specs: dict
    validation_status: bool

def validate_specs(state: AircraftState):
    required = ['MTOW', 'Payload', 'Range']
    state['validation_status'] = all(k in state['specs'] for k in required)
    return state

def check_compliance(state: AircraftState):
    if state.get('validation_status'):
        print('Checking aviation safety compliance...')
    return state

builder = StateGraph(AircraftState)
builder.add_node('validate', validate_specs)
builder.add_node('compliance', check_compliance)
builder.set_entry_point('validate')
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
graph = builder.compile()