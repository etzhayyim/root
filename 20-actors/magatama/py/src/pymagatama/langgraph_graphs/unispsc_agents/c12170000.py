from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    cas_number: str
    quantity: float
    compliance_docs: List[str]
    validation_status: bool

def validate_chemical_compliance(state: ChemicalState):
    # Simulate SDS validation logic
    is_compliant = "sds_received" in state["compliance_docs"]
    return {"validation_status": is_compliant}

def process_chemical_procurement(state: ChemicalState):
    # Simulate logistics routing for hazardous materials
    print(f"Processing procurement for CAS: {state['cas_number']}")
    return {"validation_status": True}

graph = StateGraph(ChemicalState)
graph.add_node("validate", validate_chemical_compliance)
graph.add_node("process", process_chemical_procurement)
graph.add_edge("validate", "process")
graph.add_edge("process", END)
graph.set_entry_point("validate")
app = graph.compile()