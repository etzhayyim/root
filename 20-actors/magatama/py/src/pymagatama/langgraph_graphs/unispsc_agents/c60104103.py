from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class KitState(TypedDict):
    kit_id: str
    contents: List[str]
    validation_status: bool

def validate_contents(state: KitState):
    return {"validation_status": len(state["contents"]) > 0}

def approve_kit(state: KitState):
    return {"validation_status": True}

graph = StateGraph(KitState)
graph.add_node("validate", validate_contents)
graph.add_node("approve", approve_kit)
graph.add_edge("validate", "approve")
graph.add_edge("approve", END)
graph.set_entry_point("validate")
app = graph.compile()
