from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToyState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_safety(state: ToyState):
    thresholds = {'max_load': 50, 'safety_standard': 'EN71'}
    compliant = state['spec_data'].get('load', 0) <= thresholds['max_load']
    return {'is_compliant': compliant}

builder = StateGraph(ToyState)
builder.add_node('safety_check', validate_safety)
builder.set_entry_point('safety_check')
builder.add_edge('safety_check', END)
graph = builder.compile()
