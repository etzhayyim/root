from typing import TypedDict
from langgraph.graph import StateGraph, END

class MopState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_mop_specs(state: MopState):
    required = ['material', 'attachment_type']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

workflow = StateGraph(MopState)
workflow.add_node('validate', validate_mop_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
