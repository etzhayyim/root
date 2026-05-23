from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class SeedCounterState(TypedDict):
    seed_data: dict
    validation_passed: bool
    error_log: list

def validate_sensor_data(state: SeedCounterState):
    data = state.get('seed_data', {})
    is_valid = data.get('accuracy') > 99.0
    return {'validation_passed': is_valid}

def route_processing(state: SeedCounterState):
    return 'validate' if state.get('seed_data') else END

graph = StateGraph(SeedCounterState)
graph.add_node('validate', validate_sensor_data)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
