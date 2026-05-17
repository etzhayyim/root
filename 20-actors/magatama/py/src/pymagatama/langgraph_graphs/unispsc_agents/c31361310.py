from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class TitaniumState(TypedDict):
    spec_content: str
    inspection_status: str
    compliance_score: int

def validate_welding_specs(state: TitaniumState):
    # Business logic for validating ASME welding compliance
    return {"inspection_status": "Validated" if "ASME" in state["spec_content"] else "Failed"}

def check_export_controls(state: TitaniumState):
    # Business logic for dual-use criteria
    return {"compliance_score": 100 if state["inspection_status"] == "Validated" else 0}

graph = StateGraph(TitaniumState)
graph.add_node("validate_welding", validate_welding_specs)
graph.add_node("export_compliance", check_export_controls)
graph.set_entry_point("validate_welding")
graph.add_edge("validate_welding", "export_compliance")
graph.add_edge("export_compliance", END)
graph = graph.compile()