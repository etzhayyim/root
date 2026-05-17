from typing import TypedDict
from langgraph.graph import StateGraph, END

class FiberTestState(TypedDict):
    test_range: float
    wavelength: int
    calibration_valid: bool
    is_compliant: bool

def validate_optical_specs(state: FiberTestState):
    state['is_compliant'] = state['test_range'] > 0 and state['calibration_valid']
    return {"is_compliant": state['is_compliant']}

def report_result(state: FiberTestState):
    print(f"Validation complete: {state['is_compliant']}")
    return {}

graph = StateGraph(FiberTestState)
graph.add_node("validate", validate_optical_specs)
graph.add_node("report", report_result)
graph.add_edge("validate", "report")
graph.add_edge("report", END)
graph.set_entry_point("validate")
graph = graph.compile()