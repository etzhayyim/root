from typing import TypedDict
from langgraph.graph import StateGraph, END

class TimerState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_readability_specs(state: TimerState):
    errors = []
    if state['spec_data'].get('display_size_mm', 0) < 50:
        errors.append('Display size insufficient foraccessibility requirements')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(TimerState)
graph.add_node('validate_accessibility', validate_readability_specs)
graph.set_entry_point('validate_accessibility')
graph.add_edge('validate_accessibility', END)
graph = graph.compile()
