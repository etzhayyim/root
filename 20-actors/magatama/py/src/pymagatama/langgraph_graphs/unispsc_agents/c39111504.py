from typing import TypedDict
from langgraph.graph import StateGraph, END

class LightingState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_dmx_protocol(state: LightingState):
    protocol = state['spec_data'].get('protocol')
    return {'validated': protocol == 'DMX512', 'error_log': [] if protocol == 'DMX512' else ['Invalid Protocol']}

def check_safety_compliance(state: LightingState):
    certified = state['spec_data'].get('safety_cert')
    return {'validated': state['validated'] and certified, 'error_log': state['error_log'] + ([] if certified else ['Missing Safety Cert'])}

builder = StateGraph(LightingState)
builder.add_node('dmx_check', validate_dmx_protocol)
builder.add_node('safety_check', check_safety_compliance)
builder.set_entry_point('dmx_check')
builder.add_edge('dmx_check', 'safety_check')
builder.add_edge('safety_check', END)
graph = builder.compile()
