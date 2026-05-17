from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DivingSpec(TypedDict):
    spec_id: str
    depth_limit: float
    validation_passed: bool

def validate_diving_gear(state: DivingSpec):
    state['validation_passed'] = state['depth_limit'] > 0
    return state

def safety_check(state: DivingSpec):
    print(f'Processing safety check for {state[\'spec_id\']}')
    return state

graph = StateGraph(DivingSpec)
graph.add_node('validate', validate_diving_gear)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()