from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class BinderState(TypedDict):
    commodity_code: str
    spec_data: Dict[str, Any]
    validation_errors: List[str]
    is_compliant: bool

def validate_capacity(state: BinderState) -> BinderState:
    capacity = state['spec_data'].get('sheet_capacity', 0)
    if capacity < 0: state['validation_errors'].append('Negative capacity')
    return state

def check_material(state: BinderState) -> BinderState:
    material = state['spec_data'].get('material', 'plastic')
    if material not in ['paper', 'plastic', 'metal']: state['validation_errors'].append('Unknown material')
    return state

def finalize_compliance(state: BinderState) -> BinderState:
    state['is_compliant'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(BinderState)
graph.add_node('validate_capacity', validate_capacity)
graph.add_node('check_material', check_material)
graph.add_node('finalize', finalize_compliance)
graph.set_entry_point('validate_capacity')
graph.add_edge('validate_capacity', 'check_material')
graph.add_edge('check_material', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
