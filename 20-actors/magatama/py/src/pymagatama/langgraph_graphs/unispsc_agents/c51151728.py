from typing import TypedDict
from langgraph.graph import StateGraph, END
class ChemProcurementState(TypedDict):
    chemical_name: str
    purity: float
    regulatory_approved: bool
    compliance_passed: bool
def validate_purity(state: ChemProcurementState):
    return {"compliance_passed": state['purity'] >= 0.99}
def check_regulatory(state: ChemProcurementState):
    return {"compliance_passed": state['regulatory_approved']}
graph = StateGraph(ChemProcurementState)
graph.add_node("validate_purity", validate_purity)
graph.add_node("check_regulatory", check_regulatory)
graph.set_entry_point("validate_purity")
graph.add_edge("validate_purity", "check_regulatory")
graph.add_edge("check_regulatory", END)
graph = graph.compile()