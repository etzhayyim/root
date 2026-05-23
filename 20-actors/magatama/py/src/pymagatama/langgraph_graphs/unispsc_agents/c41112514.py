from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OilGaugeState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: OilGaugeState):
    errors = []
    if state['spec_data'].get('pressure_rating', 0) <= 0:
        errors.append('Invalid pressure rating')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(OilGaugeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
