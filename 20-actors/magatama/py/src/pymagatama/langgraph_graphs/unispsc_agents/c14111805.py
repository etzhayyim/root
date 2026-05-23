from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class OfficeLabelState(TypedDict):
    label_id: str
    spec_verified: bool
    validation_log: list[str]

def validate_label_spec(state: OfficeLabelState):
    log = state.get("validation_log", [])
    log.append(f"Validating specification for label: {state['label_id']}")
    return {"spec_verified": True, "validation_log": log}

def process_procurement_workflow(state: OfficeLabelState):
    log = state.get("validation_log", [])
    log.append("Proceeding to inventory allocation.")
    return {"validation_log": log}

graph = StateGraph(OfficeLabelState)
graph.add_node("validate", validate_label_spec)
graph.add_node("process", process_procurement_workflow)
graph.add_edge("validate", "process")
graph.add_edge("process", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()
