from typing import TypedDict
from langgraph.graph import StateGraph, END

class VentState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: VentState):
    required = ['material', 'pressure_rating']
    errors = [f'Missing {f}' for f in required if f not in state['spec_data']]
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def process_vent_order(state: VentState):
    return {'validation_passed': True}

graph = StateGraph(VentState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_vent_order)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
