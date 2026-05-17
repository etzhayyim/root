from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ServoControlState(TypedDict):
    board_id: str
    specs: dict
    is_validated: bool
    validation_log: List[str]

def validate_servo_specs(state: ServoControlState):
    log = state.get("validation_log", [])
    specs = state.get("specs", {})
    if specs.get("voltage") and specs.get("protocol"):
        is_valid = True
        log.append("Basic specs verified.")
    else:
        is_valid = False
        log.append("Missing critical specs.")
    return {"is_validated": is_valid, "validation_log": log}

def compile_servo_workflow():
    graph = StateGraph(ServoControlState)
    graph.add_node("validate", validate_servo_specs)
    graph.set_entry_point("validate")
    graph.add_edge("validate", END)
    return graph.compile()