from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KitchenwareState(TypedDict):
    spec_sheet: dict
    validation_errors: List[str]
    is_approved: bool

def validate_materials(state: KitchenwareState):
    # Business logic for checking material safety standards (e.g., FDA/EU food contact compliance)
    if 'material' not in state['spec_sheet']:
        state['validation_errors'].append('Material field missing')
    return state

def check_thermal_compatibility(state: KitchenwareState):
    # Logic to verify if saucepans work with specified stovetops
    if not state['spec_sheet'].get('ih_compatible', False):
        state['validation_errors'].append('Non-induction compatible items marked for premium tier')
    return state

graph = StateGraph(KitchenwareState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_thermal', check_thermal_compatibility)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'check_thermal')
graph.add_edge('check_thermal', END)
graph = graph.compile()
