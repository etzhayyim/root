from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class LaundryBasketState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_material(state: LaundryBasketState):
    material = state.get('specs', {}).get('material', '').lower()
    if not material:
        state['validation_errors'].append('Material specification is missing.')
    return state

def check_compliance(state: LaundryBasketState):
    if not state.get('validation_errors'):
        state['is_approved'] = True
    return state

graph = StateGraph(LaundryBasketState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()