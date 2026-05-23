from typing import TypedDict
from langgraph.graph import StateGraph, END

class SextantState(TypedDict):
    instrument_id: str
    calibration_status: bool
    accuracy_check: float

def validate_instrument(state: SextantState):
    print(f'Validating sextant: {state["instrument_id"]}')
    return {"calibration_status": True}

def quality_check(state: SextantState):
    if state["accuracy_check"] < 0.5:
        return "pass"
    return "fail"

graph = StateGraph(SextantState)
graph.add_node("validate", validate_instrument)
graph.add_edge("validate", END)
graph.set_entry_point("validate")
graph = graph.compile()
