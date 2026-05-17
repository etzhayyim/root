from typing import TypedDict
from langgraph.graph import StateGraph, END

class BackgroundScreenState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: BackgroundScreenState):
    required = ['material', 'size', 'flame_retardancy']
    state['approved'] = all(k in state['specs'] for k in required)
    return state

workflow = StateGraph(BackgroundScreenState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()