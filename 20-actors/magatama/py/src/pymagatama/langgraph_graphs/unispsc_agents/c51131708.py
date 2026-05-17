from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    batch_id: str
    quality_status: str
    requires_cooling: bool

def validate_batch(state: DrugState):
    print(f'Validating batch {state["batch_id"]} for Cilostazol compliance.')
    return {"quality_status": "passed"}

workflow = StateGraph(DrugState)
workflow.add_node("validate", validate_batch)
workflow.set_entry_point("validate")
workflow.add_edge("validate", END)
graph = workflow.compile()