from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class HydraulicState(TypedDict):
    spec_data: dict
    validation_errors: list[str]
    is_approved: bool

def validate_cylinder_specs(state: HydraulicState):
    errors = []
    specs = state['spec_data']
    if specs.get('max_pressure_rating_mpa', 0) <= 0:
        errors.append('Invalid pressure rating')
    if specs.get('bore_diameter_mm', 0) <= 0:
        errors.append('Invalid bore diameter')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

def route_by_validation(state: HydraulicState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(HydraulicState)
graph.add_node('validate', validate_cylinder_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
app = graph.compile()