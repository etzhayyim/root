from typing import TypedDict
from langgraph.graph import StateGraph, END

class MillingState(TypedDict):
    spec_data: dict
    validation_results: dict

def validate_specs(state: MillingState):
    specs = state['spec_data']
    valid = all(k in specs for k in ['spindle_speed_range', 'control_system_type'])
    return {'validation_results': {'is_valid': valid, 'status': 'PASS' if valid else 'FAIL'}}

builder = StateGraph(MillingState)
builder.add_node('validate', validate_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()