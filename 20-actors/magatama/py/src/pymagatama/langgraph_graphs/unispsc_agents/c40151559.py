from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    spec_data: dict
    validation_errors: list
    status: str

def validate_simplex_specs(state: PumpState):
    errors = []
    required_fields = ['capacity', 'pressure', 'material']
    for field in required_fields:
        if field not in state['spec_data']:
            errors.append(f'Missing field: {field}')
    return {'validation_errors': errors, 'status': 'validated' if not errors else 'failed'}

def check_compliance(state: PumpState):
    return {'status': 'compliant' if state['status'] == 'validated' else 'non-compliant'}

graph = StateGraph(PumpState)
graph.add_node('validate', validate_simplex_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
