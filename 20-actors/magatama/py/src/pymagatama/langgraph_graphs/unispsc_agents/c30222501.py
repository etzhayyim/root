from typing import TypedDict
from langgraph.graph import StateGraph, END

class HousingState(TypedDict):
    address: str
    inspection_report: str
    approved: bool

def validate_compliance(state: HousingState):
    print(f'Validating zoning for {state["address"]}')
    return {"approved": True}

def finalize_contract(state: HousingState):
    print('Contract finalized')
    return {}

builder = StateGraph(HousingState)
builder.add_node("validate", validate_compliance)
builder.add_node("finalize", finalize_contract)
builder.set_entry_point("validate")
builder.add_edge("validate", "finalize")
builder.add_edge("finalize", END)
graph = builder.compile()
