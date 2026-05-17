from typing import TypedDict
from langgraph.graph import StateGraph, END

class KitchenApplianceState(TypedDict):
    model_name: str
    voltage_check: bool
    safety_certification: bool

def validate_specs(state: KitchenApplianceState) -> KitchenApplianceState:
    state['voltage_check'] = True
    state['safety_certification'] = True
    return state

def assemble_procurement_report(state: KitchenApplianceState) -> str:
    return f"Procurement ready for {state['model_name']}"

graph = StateGraph(KitchenApplianceState)
graph.add_node("validate", validate_specs)
graph.add_node("assemble", assemble_procurement_report)
graph.add_edge("validate", "assemble")
graph.add_edge("assemble", END)
graph.set_entry_point("validate")