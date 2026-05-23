from typing import TypedDict
from langgraph.graph import StateGraph, END

class ConnectorState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: ConnectorState):
    specs = state['spec_data']
    errors = []
    if 'category' not in specs or specs['category'] not in ['Cat5e', 'Cat6', 'Cat6A']:
        errors.append('Invalid network category')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

graph = StateGraph(ConnectorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
