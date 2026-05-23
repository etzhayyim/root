from typing import TypedDict
from langgraph.graph import StateGraph, END

class KitchenwareState(TypedDict):
    spec_data: dict
    approved: bool

def validate_materials(state: KitchenwareState):
    material = state['spec_data'].get('material', '')
    is_food_safe = material in ['304 Stainless Steel', 'Anodized Aluminum']
    return {'approved': is_food_safe}

def check_compliance(state: KitchenwareState):
    has_nsf = state['spec_data'].get('nsf_certified', False)
    return {'approved': state['approved'] and has_nsf}

graph = StateGraph(KitchenwareState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
