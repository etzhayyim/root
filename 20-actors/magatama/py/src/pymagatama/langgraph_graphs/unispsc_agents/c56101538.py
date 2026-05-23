from typing import TypedDict
from langgraph.graph import StateGraph, END

class BuffetState(TypedDict):
    spec_data: dict
    validation_results: list

def validate_furniture_spec(state: BuffetState):
    fields = ["material", "dimensions", "fire_safety"]
    valid = all(key in state['spec_data'] for key in fields)
    return {"validation_results": ["Pass" if valid else "Fail"]}

def route_by_validation(state: BuffetState):
    return "end" if state['validation_results'][0] == "Pass" else "end"

graph = StateGraph(BuffetState)
graph.add_node("validate", validate_furniture_spec)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
compiled_graph = graph.compile()
