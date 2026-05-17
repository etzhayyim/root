from typing import TypedDict
from langgraph.graph import StateGraph, END

class HardwareState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: HardwareState):
    required = ['interface', 'rate']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required specs'}

def process_network_unit(state: HardwareState):
    print('Configuring network unit parameters...')
    return {'validated': True}

builder = StateGraph(HardwareState)
builder.add_node('validate', validate_specs)
builder.add_node('process', process_network_unit)
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
builder.set_entry_point('validate')
graph = builder.compile()