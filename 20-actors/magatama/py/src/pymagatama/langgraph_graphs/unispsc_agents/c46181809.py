from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_materials(state: ProcurementState):
    material = state.get('spec_data', {}).get('material', '')
    if not material:
        state['validation_errors'].append('Material specification missing.')
    return state

def check_compliance(state: ProcurementState):
    if not state.get('validation_errors'):
        state['is_approved'] = True
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()