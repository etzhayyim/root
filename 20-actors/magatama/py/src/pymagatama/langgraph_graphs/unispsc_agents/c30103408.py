from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CopperState(TypedDict):
    purity: float
    weight_kg: float
    verified: bool

def validate_ingot(state: CopperState):
    if state['purity'] >= 99.9:
        state['verified'] = True
    else:
        state['verified'] = False
    return state

graph = StateGraph(CopperState)
graph.add_node("validate", validate_ingot)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()
