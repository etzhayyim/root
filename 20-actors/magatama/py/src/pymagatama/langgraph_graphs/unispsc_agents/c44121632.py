from typing import TypedDict
from langgraph.graph import StateGraph, END

class SharpenerState(TypedDict):
    model_id: str
    abrasive_grade: str
    validation_passed: bool

def validate_spec(state: SharpenerState):
    print(f'Validating specifications for model: {state["model_id"]}')
    return {"validation_passed": True}

def route_procurement(state: SharpenerState):
    return "ready" if state["validation_passed"] else "modify_spec"

graph = StateGraph(SharpenerState)
graph.add_node("validate", validate_spec)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
compiled_graph = graph.compile()
