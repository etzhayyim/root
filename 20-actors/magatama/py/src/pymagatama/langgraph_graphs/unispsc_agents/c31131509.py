from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BerylliumForgeState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    certification_passed: bool

def validate_aerospace_specs(state: BerylliumForgeState):
    errors = []
    if "grade" not in state["spec_data"]: errors.append("Missing material grade")
    if not state["spec_data"].get("is_toxic_compliant", False): errors.append("Toxicity safety missing")
    return {"validation_errors": errors, "certification_passed": len(errors) == 0}

def export_review(state: BerylliumForgeState):
    print("Triggering dual-use export control review workflow...")
    return {"certification_passed": state["certification_passed"]}

graph = StateGraph(BerylliumForgeState)
graph.add_node("validate", validate_aerospace_specs)
graph.add_node("export_compliance", export_review)
graph.set_entry_point("validate")
graph.add_edge("validate", "export_compliance")
graph.add_edge("export_compliance", END)
graph = graph.compile()
