from typing import TypedDict
from langgraph.graph import StateGraph, END

class ContainerState(TypedDict):
    capacity: float
    material: str
    is_leak_tested: bool
    compliant: bool

def validate_container(state: ContainerState):
    state['compliant'] = state['capacity'] > 0 and state['is_leak_tested']
    return state

workflow = StateGraph(ContainerState)
workflow.add_node("validate", validate_container)
workflow.set_entry_point("validate")
workflow.add_edge("validate", END)
graph = workflow.compile()