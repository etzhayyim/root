from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PrintGraphState(TypedDict):
    material_type: str
    compliance_docs: List[str]
    validation_complete: bool

def validate_materials(state: PrintGraphState):
    # Simulate material safety check logic for printmaking chemicals
    has_msds = "MSDS" in state.get("compliance_docs", [])
    print(f"Material validation check for {state['material_type']}: {has_msds}")
    return {"validation_complete": has_msds}

graph = StateGraph(PrintGraphState)
graph.add_node("validate", validate_materials)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()
