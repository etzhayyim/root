from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    batch_id: str
    purity_level: float
    safety_check_passed: bool
    log: Annotated[list[str], operator.add]

def validate_purity(state: ChemicalState) -> ChemicalState:
    passed = state['purity_level'] >= 99.9
    return {"safety_check_passed": passed, "log": [f"Purity validation: {passed}"]}

def check_hazard_compliance(state: ChemicalState) -> ChemicalState:
    return {"log": ["Hazard compliance verified for organic salt batch"]}

graph = StateGraph(ChemicalState)
graph.add_node("validate_purity", validate_purity)
graph.add_node("check_hazard", check_hazard_compliance)
graph.set_entry_point("validate_purity")
graph.add_edge("validate_purity", "check_hazard")
graph.add_edge("check_hazard", END)
graph = graph.compile()