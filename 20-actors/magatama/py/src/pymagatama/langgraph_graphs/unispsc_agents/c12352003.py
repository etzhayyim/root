from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    purity: float
    safety_check: bool
    compilation_status: str

def validate_purity(state: CatalystState):
    return {"safety_check": state["purity"] >= 99.9}

def compile_catalyst_workflow(state: CatalystState):
    if state["safety_check"]:
        return {"compilation_status": "SUCCESS_COMPILED"}
    return {"compilation_status": "FAILED_PURITY_REJECT"}

graph = StateGraph(CatalystState)
graph.add_node("validate", validate_purity)
graph.add_node("compile", compile_catalyst_workflow)
graph.set_entry_point("validate")
graph.add_edge("validate", "compile")
graph.add_edge("compile", END)
compiled_graph = graph.compile()