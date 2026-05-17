from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SiliconState(TypedDict):
    purity: float
    resistivity: float
    status: str
    validation_log: List[str]

def validate_silicon_specs(state: SiliconState):
    log = []
    status = "validated"
    if state["purity"] < 99.999:
        status = "rejected"
        log.append("Purity below threshold for semiconductor grade.")
    return {"status": status, "validation_log": log}

def prepare_shipping(state: SiliconState):
    return {"status": "shipped"}

graph = StateGraph(SiliconState)
graph.add_node("validate", validate_silicon_specs)
graph.add_node("ship", prepare_shipping)
graph.set_entry_point("validate")
graph.add_conditional_edges("validate", lambda s: "ship" if s["status"] == "validated" else END, {"ship": "ship", "__end__": END})
graph.add_edge("ship", END)
graph = graph.compile()