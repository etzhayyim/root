from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MachineToolState(TypedDict):
    part_id: str
    tolerance_check: bool
    specs: List[str]
    approved: bool

def validate_specs(state: MachineToolState):
    # Simulate CAD/Spec validation logic
    state['tolerance_check'] = True if len(state['specs']) > 2 else False
    return state

def approval_check(state: MachineToolState):
    state['approved'] = state['tolerance_check']
    return state

graph = StateGraph(MachineToolState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
