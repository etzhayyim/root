from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PurificationState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: PurificationState):
    errors = []
    if state['spec_data'].get('uv_intensity', 0) < 30 :
        errors.append('UV intensity below safety threshold')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_compliance(state: PurificationState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(PurificationState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
