from typing import TypedDict
from langgraph.graph import StateGraph, END

class PrintingWipeState(TypedDict):
    wipe_type: str
    solvent_compatibility: str
    quality_check_passed: bool

def validate_wipe_specs(state: PrintingWipeState):
    # Business logic for verifying if the wipes meet printing standards
    if state.get("solvent_compatibility") in ["Toluene", "Xylene", "Mineral Spirits"]:
        return {"quality_check_passed": True}
    return {"quality_check_passed": False}

def finalize_order(state: PrintingWipeState):
    print(f"Finalizing order for {state['wipe_type']}. Status: {state['quality_check_passed']}")
    return {}

graph = StateGraph(PrintingWipeState)
graph.add_node("validate", validate_wipe_specs)
graph.add_node("finalize", finalize_order)
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
graph.set_entry_point("validate")
graph = graph.compile()