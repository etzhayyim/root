from typing import TypedDict
from langgraph.graph import StateGraph, END

class SewingKitState(TypedDict):
    kit_components: list
    validation_status: bool

def validate_components(state: SewingKitState):
    required = ['needle', 'thread']
    status = all(item in state['kit_components'] for item in required)
    return {'validation_status': status}

workflow = StateGraph(SewingKitState)
workflow.add_node('validate', validate_components)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()