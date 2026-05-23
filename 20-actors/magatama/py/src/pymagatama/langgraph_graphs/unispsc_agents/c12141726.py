from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ResinProcessingState(TypedDict):
    resin_id: str
    purity_level: float
    safety_check_passed: bool
    compliance_tags: List[str]
    steps_completed: List[str]

def validate_purity(state: ResinProcessingState):
    passed = state['purity_level'] >= 99.5
    return {"safety_check_passed": passed, "steps_completed": state['steps_completed'] + ["purity_check"]}

def route_by_safety(state: ResinProcessingState):
    return "compliant_flow" if state['safety_check_passed'] else END

def perform_processing(state: ResinProcessingState):
    return {"steps_completed": state['steps_completed'] + ["chemical_processing_complete"]}

graph = StateGraph(ResinProcessingState)
graph.add_node("validate", validate_purity)
graph.add_node("process", perform_processing)
graph.add_edge("validate", "process")
graph.add_edge("process", END)
graph.set_entry_point("validate")
graph = graph.compile()
