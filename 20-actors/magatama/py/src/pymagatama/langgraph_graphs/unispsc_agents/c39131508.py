from typing import TypedDict
from langgraph.graph import StateGraph, END

class WireMarkerState(TypedDict):
    marker_type: str
    material_spec: str
    is_compliant: bool

def validate_materials(state: WireMarkerState):
    # Business logic for verifying if adhesive meets industrial standards
    state['is_compliant'] = 'industrial_grade' in state['material_spec']
    return state

def check_dispenser_fit(state: WireMarkerState):
    # Logic to verify roll compatibility with existing inventory
    return {'is_compliant': state['is_compliant']}

workflow = StateGraph(WireMarkerState)
workflow.add_node('validate', validate_materials)
workflow.add_node('fit_check', check_dispenser_fit)
workflow.add_edge('validate', 'fit_check')
workflow.add_edge('fit_check', END)
workflow.set_entry_point('validate')
graph = workflow.compile()
