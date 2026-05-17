from typing import TypedDict
from langgraph.graph import StateGraph, END

class HookState(TypedDict):
    load_capacity_kg: float
    material: str
    is_compliant: bool

def validate_hook_specs(state: HookState):
    # Business logic for hook safety certification validation
    if state['load_capacity_kg'] > 0 and state['material'] in ['Steel', 'Stainless Steel']:
        return {'is_compliant': True}
    return {'is_compliant': False}

def approval_step(state: HookState):
    return {**state}

graph = StateGraph(HookState)
graph.add_node('validate', validate_hook_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()