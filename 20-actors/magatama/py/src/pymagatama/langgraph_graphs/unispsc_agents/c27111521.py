from langgraph.graph import StateGraph, END
from typing import TypedDict
class NibblerState(TypedDict):
    spec_data: dict
    validation_errors: list
    status: str
def validate_specs(state: NibblerState):
    errors = []
    if not state['spec_data'].get('cutting_capacity'):
        errors.append('Missing required field: cutting_capacity')
    return {'validation_errors': errors, 'status': 'validated' if not errors else 'failed'}
def route_step(state: NibblerState):
    return 'validate' if state['status'] == 'pending' else END
graph = StateGraph(NibblerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
