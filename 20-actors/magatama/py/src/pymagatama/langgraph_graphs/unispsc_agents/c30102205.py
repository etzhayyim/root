from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SteelProcurementState(TypedDict):
    grade: str
    thickness: float
    certification_required: bool
    validation_passed: bool

def validate_specs(state: SteelProcurementState):
    state['validation_passed'] = state['grade'] in ['SUS304', 'SUS316'] and state['thickness'] > 0
    return state

workflow = StateGraph(SteelProcurementState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
