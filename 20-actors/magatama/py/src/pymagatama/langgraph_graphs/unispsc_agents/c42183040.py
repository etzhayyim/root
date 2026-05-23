from typing import TypedDict
from langgraph.graph import StateGraph, END

class OpticianState(TypedDict):
    tool_id: str
    is_calibrated: bool
    validation_report: str

def validate_specs(state: OpticianState):
    print(f'Validating optical tool: {state["tool_id"]}')
    return {"validation_report": "Compliance Verified" if state["is_calibrated"] else "Calibration Required"}

workflow = StateGraph(OpticianState)
workflow.add_node("validate", validate_specs)
workflow.set_entry_point("validate")
workflow.add_edge("validate", END)
graph = workflow.compile()
