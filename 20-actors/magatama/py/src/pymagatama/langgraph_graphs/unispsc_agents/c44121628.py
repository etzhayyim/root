from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_id: str
    specs: dict
    approved: bool

def validate_specs(state: ProcurementState):
    required = ['material_composition', 'base_stability']
    state['approved'] = all(k in state['specs'] for k in required)
    return state

workflow = StateGraph(ProcurementState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
