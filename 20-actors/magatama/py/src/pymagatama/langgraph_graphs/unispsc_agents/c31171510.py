from typing import TypedDict, List
from langgraph.graph import StateGraph

class BearingState(TypedDict):
    spec_sheet: dict
    validation_errors: List[str]
    is_approved: bool

def validate_load_ratings(state: BearingState):
    errors = []
    if state['spec_sheet'].get('dynamic_load') <= 0:
        errors.append('Invalid dynamic load rating')
    return {'validation_errors': errors}

def check_material_compliance(state: BearingState):
    is_ok = state['spec_sheet'].get('material') in ['Steel', 'Bronze', 'Stainless Steel']
    return {'is_approved': is_ok}

graph = StateGraph(BearingState)
graph.add_node('validate_load', validate_load_ratings)
graph.add_node('check_material', check_material_compliance)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'check_material')
graph.add_edge('check_material', '__end__')
graph = graph.compile()
