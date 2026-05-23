from typing import TypedDict
from langgraph.graph import StateGraph, END

class ConnectorState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_pressure_rating(state: ConnectorState) -> ConnectorState:
    rating = state.get('spec_data', {}).get('pressure_rating', 0)
    if rating > 0:
        state['validation_passed'] = True
    else:
        state['validation_passed'] = False
        state['error_log'].append('Invalid pressure rating provided.')
    return state

workflow = StateGraph(ConnectorState)
workflow.add_node('validate', validate_pressure_rating)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
