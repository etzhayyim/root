from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DishwasherState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: DishwasherState):
    errors = []
    if state['spec_data'].get('power_phase') not in ['3-phase', '1-phase']:
        errors.append('Invalid power specification')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph_builder = StateGraph(DishwasherState)
graph_builder.add_node('validator', validate_specs)
graph_builder.set_entry_point('validator')
graph_builder.add_edge('validator', END)
graph = graph_builder.compile()