from typing import TypedDict
from langgraph.graph import StateGraph, END

class BalanceState(TypedDict):
    model_number: str
    calibration_status: bool
    accuracy_verified: bool

def check_calibration(state: BalanceState):
    print(f"Verifying calibration for {state['model_number']}")
    return {"calibration_status": True}

def validate_specs(state: BalanceState):
    print("Validating laboratory accuracy requirements")
    return {"accuracy_verified": True}

graph = StateGraph(BalanceState)
graph.add_node("check_cal", check_calibration)
graph.add_node("validate_acc", validate_specs)
graph.set_entry_point("check_cal")
graph.add_edge("check_cal", "validate_acc")
graph.add_edge("validate_acc", END)
graph = graph.compile()
