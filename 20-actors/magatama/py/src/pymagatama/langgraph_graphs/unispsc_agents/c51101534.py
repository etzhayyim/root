from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    reagent_id: str
    quality_checks: List[str]
    is_cleared: bool

def validate_cold_chain(state: ReagentState):
    print(f"Validating storage conditions for {state['reagent_id']}")
    return {"quality_checks": state["quality_checks"] + ["cold_chain_ok"]}

def perform_assay(state: ReagentState):
    print(f"Performing analytical assay for {state['reagent_id']}")
    return {"quality_checks": state["quality_checks"] + ["assay_passed"], "is_cleared": True}

graph = StateGraph(ReagentState)
graph.add_node("validate", validate_cold_chain)
graph.add_node("assay", perform_assay)
graph.set_entry_point("validate")
graph.add_edge("validate", "assay")
graph.add_edge("assay", END)
graph = graph.compile()