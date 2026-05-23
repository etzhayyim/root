from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ConcreteSpecState(TypedDict):
    strength: float
    absorption: float
    verified: bool

def validate_quality(state: ConcreteSpecState):
    state['verified'] = state['strength'] > 30.0 and state['absorption'] < 5.0
    return state

def process_delivery(state: ConcreteSpecState):
    return {"verified": state['verified']}

graph = StateGraph(ConcreteSpecState)
graph.add_node("validate", validate_quality)
graph.add_node("process", process_delivery)
graph.add_edge("validate", "process")
graph.add_edge("process", END)
graph.set_entry_point("validate")
graph = graph.compile()
