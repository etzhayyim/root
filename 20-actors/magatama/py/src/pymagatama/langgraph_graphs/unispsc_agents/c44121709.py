from typing import TypedDict
from langgraph.graph import StateGraph, END

class CrayonState(TypedDict):
    brand: str
    non_toxic: bool
    passed_qa: bool

def validate_safety(state: CrayonState):
    state['passed_qa'] = state['non_toxic']
    return state

def quality_check(state: CrayonState):
    print(f'Checking quality for {state.get("brand")}')
    return state

graph = StateGraph(CrayonState)
graph.add_node('safety_check', validate_safety)
graph.add_node('quality_check', quality_check)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'quality_check')
graph.add_edge('quality_check', END)

graph = graph.compile()