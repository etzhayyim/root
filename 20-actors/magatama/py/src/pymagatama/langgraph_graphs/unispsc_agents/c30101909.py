from typing import TypedDict
from langgraph.graph import StateGraph, END

class CopperProcurementState(TypedDict):
    purity: float
    thickness: float
    is_compliant: bool

def validate_specs(state: CopperProcurementState):
    state['is_compliant'] = state['purity'] >= 99.9 and state['thickness'] > 0
    return state

workflow = StateGraph(CopperProcurementState)
workflow.add_node('validation', validate_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
