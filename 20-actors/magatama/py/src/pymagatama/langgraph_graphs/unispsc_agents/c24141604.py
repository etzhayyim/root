from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WaddingState(TypedDict):
    material_type: str
    density_check: bool
    flammability_compliant: bool
    approved: bool

def validate_materials(state: WaddingState):
    state['density_check'] = True if state.get('density') > 50 else False
    return state

def check_compliance(state: WaddingState):
    state['approved'] = state['density_check'] and state['flammability_compliant']
    return state

workflow = StateGraph(WaddingState)
workflow.add_node('validate', validate_materials)
workflow.add_node('compliance', check_compliance)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'compliance')
workflow.add_edge('compliance', END)
graph = workflow.compile()