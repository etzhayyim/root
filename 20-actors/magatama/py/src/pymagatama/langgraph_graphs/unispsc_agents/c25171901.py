from typing import TypedDict
from langgraph.graph import StateGraph, END

class WheelProcurementState(TypedDict):
    spec_data: dict
    validation_result: bool

def validate_specs(state: WheelProcurementState):
    required_keys = ['material', 'load_rating', 'bolt_pattern']
    valid = all(k in state['spec_data'] for k in required_keys)
    return {'validation_result': valid}

def process_procurement(state: WheelProcurementState):
    print('Initiating wheel procurement workflow...')
    return state

builder = StateGraph(WheelProcurementState)
builder.add_node('validate', validate_specs)
builder.add_node('process', process_procurement)
builder.set_entry_point('validate')
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
graph = builder.compile()
