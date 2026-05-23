from typing import TypedDict
from langgraph.graph import StateGraph, END

class IncubatorState(TypedDict):
    specs: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: IncubatorState):
    s = state['specs']
    valid = all([s.get('co2_range'), s.get('humidity_range'), s.get('volume_liters') > 0])
    return {'validation_passed': valid}

def route_by_validation(state: IncubatorState):
    return 'validate' if not state.get('validation_passed') else 'end'

graph = StateGraph(IncubatorState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
