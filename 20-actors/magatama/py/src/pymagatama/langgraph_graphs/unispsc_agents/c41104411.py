from typing import TypedDict
from langgraph.graph import StateGraph, END

class IncubatorState(TypedDict):
    specs: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: IncubatorState):
    required = ['temperature_range_celsius', 'co2_concentration_range']
    missing = [f for f in required if f not in state['specs']]
    return {'validation_passed': len(missing) == 0, 'error_log': missing}

def check_compliance(state: IncubatorState):
    return {'validation_passed': True if state['validation_passed'] else False}

graph = StateGraph(IncubatorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
