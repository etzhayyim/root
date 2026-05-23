from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class SemiconductorChemState(TypedDict):
    material_id: str
    purity_validated: bool
    safety_check_passed: bool
    process_steps: Annotated[list[str], operator.add]

def validate_purity(state: SemiconductorChemState) -> SemiconductorChemState:
    print(f"Validating chemical purity for {state['material_id']}")
    return {'purity_validated': True, 'process_steps': ['purity_verification']}

def perform_safety_review(state: SemiconductorChemState) -> SemiconductorChemState:
    print(f"Performing safety review for {state['material_id']}")
    return {'safety_check_passed': True, 'process_steps': ['safety_inspection']}

graph = StateGraph(SemiconductorChemState)
graph.add_node("validate_purity", validate_purity)
graph.add_node("safety_review", perform_safety_review)
graph.set_entry_point("validate_purity")
graph.add_edge("validate_purity", "safety_review")
graph.add_edge("safety_review", END)
graph = graph.compile()
