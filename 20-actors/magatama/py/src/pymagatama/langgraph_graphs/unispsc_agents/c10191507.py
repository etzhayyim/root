from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class CanolaState(TypedDict):
    commodity_id: str
    batch_id: str
    purity_level: float
    status: str
    validation_log: Annotated[List[str], add_messages]

def validate_purity(state: CanolaState):
    log = f"Validating purity level for {state['batch_id']}"
    status = "ACCEPTED" if state['purity_level'] >= 99.5 else "REJECTED"
    return {"status": status, "validation_log": [log]}

def finalize_batch(state: CanolaState):
    log = f"Batch {state['batch_id']} processing completed with status {state['status']}"
    return {"validation_log": [log]}

graph = StateGraph(CanolaState)
graph.add_node("validate", validate_purity)
graph.add_node("finalize", finalize_batch)
graph.set_entry_point("validate")
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
graph = graph.compile()