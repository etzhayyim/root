from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ForgeProcurementState(TypedDict):
    part_specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_materials(state: ForgeProcurementState):
    if 'alloy_grade' not in state['part_specs']:
        state['validation_errors'].append('Missing alloy grade')
    return state

def check_dimensions(state: ForgeProcurementState):
    # Simulated CAD tolerance check logic
    return state

workflow = StateGraph(ForgeProcurementState)
workflow.add_node('validate', validate_materials)
workflow.add_node('dimensions', check_dimensions)
workflow.add_edge('validate', 'dimensions')
workflow.add_edge('dimensions', END)
workflow.set_entry_point('validate')
graph = workflow.compile()
