from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolProcessState(TypedDict):
    material: str
    spec_compliant: bool
    approved: bool

def validate_hardness(state: ToolProcessState):
    # Business logic for hardness validation
    state['spec_compliant'] = state['material'] == 'HSS'
    return state

def approval_check(state: ToolProcessState):
    state['approved'] = state['spec_compliant']
    return 'end'

graph = StateGraph(ToolProcessState)
graph.add_node('validate', validate_hardness)
graph.add_node('approval', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()