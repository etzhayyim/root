from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KitState(TypedDict):
    kit_id: str
    components: List[str]
    validation_status: bool
    expiry_check: bool

def validate_components(state: KitState):
    state['validation_status'] = len(state['components']) > 0
    return state

def check_expiry(state: KitState):
    state['expiry_check'] = True
    return state

graph = StateGraph(KitState)
graph.add_node('validate', validate_components)
graph.add_node('expiry', check_expiry)
graph.add_edge('validate', 'expiry')
graph.add_edge('expiry', END)
graph.set_entry_point('validate')
graph = graph.compile()