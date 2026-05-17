from typing import TypedDict
from langgraph.graph import StateGraph, END

class HookState(TypedDict):
    material: str
    max_load: float
    verified: bool

def validate_hook_specs(state: HookState) -> HookState:
    print(f"Validating hook specs for {state['material']}...")
    state['verified'] = state['max_load'] > 0
    return state

def check_compliance(state: HookState) -> str:
    return 'verified' if state['verified'] else 'failed'

graph = StateGraph(HookState)
graph.add_node('validate', validate_hook_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph.add_edge('', 'validate')
app = graph.compile()