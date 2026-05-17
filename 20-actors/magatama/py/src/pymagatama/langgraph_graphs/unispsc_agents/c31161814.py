from typing import TypedDict
from langgraph.graph import StateGraph, END

class WasherState(TypedDict):
    material: str
    thickness: float
    tolerance: float
    is_compliant: bool

def validate_specs(state: WasherState):
    # Business logic for thrust washer compliance
    compliant = (state['tolerance'] <= 0.05) and (state['material'] != 'unknown')
    return {**state, 'is_compliant': compliant}

def router(state: WasherState):
    return 'process' if state['is_compliant'] else 'reject'

workflow = StateGraph(WasherState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_conditional_edges('validate', router, {'process': END, 'reject': END})
graph = workflow.compile()