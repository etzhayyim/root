from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GumState(TypedDict):
    material_name: str
    viscosity: float
    has_sds: bool
    is_approved: bool

def validate_gum_specs(state: GumState):
    approved = state['has_sds'] and 1.0 <= state['viscosity'] <= 1000.0
    return {'is_approved': approved}

def approval_step(state: GumState):
    print(f'Processing {state["material_name"]}: Approval status is {state["is_approved"]}')
    return state

workflow = StateGraph(GumState)
workflow.add_node('validate', validate_gum_specs)
workflow.add_node('approve', approval_step)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'approve')
workflow.add_edge('approve', END)
graph = workflow.compile()
