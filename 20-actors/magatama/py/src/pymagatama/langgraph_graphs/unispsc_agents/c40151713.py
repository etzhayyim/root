from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpLinerState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: PumpLinerState):
    required = ['Material Grade', 'Hardness Rating']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def process_procurement(state: PumpLinerState):
    if state['validation_passed']:
        print('Proceeding to procurement workflow')
    return {}

builder = StateGraph(PumpLinerState)
builder.add_node('validate', validate_specs)
builder.add_node('process', process_procurement)
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
builder.set_entry_point('validate')
graph = builder.compile()