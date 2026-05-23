from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChamberState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_specs(state: ChamberState):
    errors = []
    if 'temperature_range' not in state['spec_data']:
        errors.append('Missing temperature range')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(ChamberState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
