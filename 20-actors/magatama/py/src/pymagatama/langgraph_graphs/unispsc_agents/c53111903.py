from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ShoeProcurementState(TypedDict):
    product_specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: ShoeProcurementState):
    errors = []
    if not state['product_specs'].get('size_range'):
        errors.append('Missing size range')
    if not state['product_specs'].get('material_composition'):
        errors.append('Missing material composition')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(ShoeProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()