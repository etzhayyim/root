from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FlowmeterState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_errors: List[str]

def validate_specs(state: FlowmeterState):
    errors = []
    if state['specs'].get('pressure_rating', 0) < 1.0:
        errors.append('Insufficient pressure rating')
    return {'is_compliant': len(errors) == 0, 'validation_errors': errors}

def check_compliance(state: FlowmeterState) -> str:
    return 'valid' if state['is_compliant'] else 'invalid'

graph = StateGraph(FlowmeterState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
