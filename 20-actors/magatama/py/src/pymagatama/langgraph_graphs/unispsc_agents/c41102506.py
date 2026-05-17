from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    validation_errors: list
    status: str

def validate_trays(state: ProcurementState):
    errors = []
    if not state['spec_data'].get('material'):
        errors.append('Missing material specification')
    return {'validation_errors': errors, 'status': 'validated' if not errors else 'failed'}

def graph_builder():
    graph = StateGraph(ProcurementState)
    graph.add_node('validate', validate_trays)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()

graph = graph_builder()