from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CurtainSpecState(TypedDict):
    dimensions: dict
    fire_safety_cert: bool
    fabric_approved: bool

def validate_dimensions(state: CurtainSpecState):
    return {"dimensions": state['dimensions']}

def check_compliance(state: CurtainSpecState):
    state['fire_safety_cert'] = True
    return state

graph = StateGraph(CurtainSpecState)
graph.add_node("validate", validate_dimensions)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
compiled_graph = graph.compile()