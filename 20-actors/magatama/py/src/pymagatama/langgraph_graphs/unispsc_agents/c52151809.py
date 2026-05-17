from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KitchenwareState(TypedDict):
    product_id: str
    specs: dict
    approved: bool
    validation_errors: List[str]

def validate_material_safety(state: KitchenwareState):
    errors = []
    if 'pfos' in state['specs'].get('coating', '').lower():
        errors.append('PFOS detected in coating.')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(KitchenwareState)
graph.add_node('validate', validate_material_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()