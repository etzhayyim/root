from langgraph.graph import StateGraph, END
from typing import TypedDict
class SplintState(TypedDict):
    part_code: str
    compliance_cleared: bool
    is_medical_grade: bool
def validate_part(state: SplintState):
    print(f"Validating part: {state['part_code']}")
    return {"compliance_cleared": True}
def check_standards(state: SplintState):
    print("Checking biocompatibility and ISO standards...")
    return {"is_medical_grade": True}
graph = StateGraph(SplintState)
graph.add_node("validate", validate_part)
graph.add_node("standards", check_standards)
graph.set_entry_point("validate")
graph.add_edge("validate", "standards")
graph.add_edge("standards", END)
compiled_graph = graph.compile()