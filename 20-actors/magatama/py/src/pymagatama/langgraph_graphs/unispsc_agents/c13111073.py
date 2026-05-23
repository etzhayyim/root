from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class GasSupplyState(TypedDict):
    pressure: float
    calorific_value: float
    safety_certs: List[str]
    validation_logs: Annotated[List[str], add_messages]

def check_safety_compliance(state: GasSupplyState) -> GasSupplyState:
    logs = [f'Verifying safety for {len(state["safety_certs"])} certificates']
    return {"validation_logs": logs}

def validate_gas_quality(state: GasSupplyState) -> GasSupplyState:
    if state['calorific_value'] < 35.0:
        return {"validation_logs": ["Low calorific value detected"]}
    return {"validation_logs": ["Quality check passed"]}

workflow = StateGraph(GasSupplyState)
workflow.add_node("safety", check_safety_compliance)
workflow.add_node("quality", validate_gas_quality)
workflow.add_edge("safety", "quality")
workflow.add_edge("quality", END)
workflow.set_entry_point("safety")
graph = workflow.compile()
