from typing import TypedDict
from langgraph.graph import StateGraph, END

class ConnectorState(TypedDict):
    spec_data: dict
    validation_result: bool
    error_log: list

def validate_specs(state: ConnectorState):
    specs = state['spec_data']
    errors = []
    if 'voltage_rating' not in specs: errors.append('Missing voltage rating')
    if 'current_rating' not in specs: errors.append('Missing current rating')
    return {'validation_result': len(errors) == 0, 'error_log': errors}

graph = StateGraph(ConnectorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
