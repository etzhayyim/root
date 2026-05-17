from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MiningComponentState(TypedDict):
    component_id: str
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_component_specs(state: MiningComponentState):
    errors = []
    if not state['spec_data'].get('material_composition'):
        errors.append('Missing material specs')
    if state['spec_data'].get('tensile_strength', 0) < 500:
        errors.append('Tensile strength below threshold')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def approve_procurement(state: MiningComponentState):
    return {'is_compliant': True}

graph = StateGraph(MiningComponentState)
graph.add_node('validator', validate_component_specs)
graph.add_node('approver', approve_procurement)
graph.set_entry_point('validator')
graph.add_edge('validator', 'approver')
graph.add_edge('approver', END)
graph = graph.compile()