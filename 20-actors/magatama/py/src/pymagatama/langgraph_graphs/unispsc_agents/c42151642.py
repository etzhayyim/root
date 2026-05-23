from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GingivectomySpec(TypedDict):
    material: str
    is_sterile: bool
    validation_tokens: List[str]

def validate_material(state: GingivectomySpec):
    return {"validation_tokens": state.get("validation_tokens", []) + ["MAT_OK"]}

def check_sterility(state: GingivectomySpec):
    status = "OK" if state["is_sterile"] else "FAIL"
    return {"validation_tokens": state.get("validation_tokens", []) + [f"STERILE_{status}"]}

graph = StateGraph(GingivectomySpec)
graph.add_node("validate_mat", validate_material)
graph.add_node("check_ster", check_sterility)
graph.set_entry_point("validate_mat")
graph.add_edge("validate_mat", "check_ster")
graph.add_edge("check_ster", END)
graph = graph.compile()
