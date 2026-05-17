from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BarenState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: BarenState):
    errors = []
    if not state['spec_data'].get('shore_hardness'):
        errors.append('Missing Shore hardness rating')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def route_verification(state: BarenState):
    return 'approved' if state['approved'] else END

graph = StateGraph(BarenState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()