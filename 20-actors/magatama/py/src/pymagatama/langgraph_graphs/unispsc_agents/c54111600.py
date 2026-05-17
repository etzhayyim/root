from typing import TypedDict
from langgraph.graph import StateGraph, END

class ClockState(TypedDict):
    spec_data: dict
    validation_errors: list

def validate_precision(state: ClockState):
    errors = state.get('validation_errors', [])
    if state['spec_data'].get('accuracy_ms', 0) > 1000:
        errors.append('Time accuracy exceeds acceptable tolerance')
    return {'validation_errors': errors}

def process_clock_spec(state: ClockState):
    return state

graph = StateGraph(ClockState)
graph.add_node('validate', validate_precision)
graph.add_node('process', process_clock_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()