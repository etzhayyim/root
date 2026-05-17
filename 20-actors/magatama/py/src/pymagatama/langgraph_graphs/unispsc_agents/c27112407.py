from typing import TypedDict
from langgraph.graph import StateGraph, END

class DetacherState(TypedDict):
    model_id: str
    compatibility_verified: bool
    safety_check_passed: bool

def check_compatibility(state: DetacherState):
    state['compatibility_verified'] = state['model_id'].startswith('SEC-')
    return state

def verify_safety(state: DetacherState):
    state['safety_check_passed'] = True
    return state

graph = StateGraph(DetacherState)
graph.add_node('verify_compatibility', check_compatibility)
graph.add_node('verify_safety', verify_safety)
graph.set_entry_point('verify_compatibility')
graph.add_edge('verify_compatibility', 'verify_safety')
graph.add_edge('verify_safety', END)
graph = graph.compile()