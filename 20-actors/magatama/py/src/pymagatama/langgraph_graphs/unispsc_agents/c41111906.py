from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChartRecorderState(TypedDict):
    specs: dict
    validation_log: list
    is_compliant: bool

def validate_specs(state: ChartRecorderState):
    # Simulate validation logic for chart recorder specifications
    is_valid = 'Calibration Certificate' in state['specs'] and state['specs'].get('accuracy') is not None
    return {'is_compliant': is_valid, 'validation_log': ['Calibration check passed'] if is_valid else ['Missing req specs']}

def route_by_compliance(state: ChartRecorderState):
    return 'process_data' if state['is_compliant'] else END

builder = StateGraph(ChartRecorderState)
builder.add_node('validate', validate_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()