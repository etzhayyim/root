from typing import TypedDict
from langgraph.graph import StateGraph, END

class PreservationState(TypedDict):
    specimen_id: str
    chemical_safety_verified: bool
    is_sterile: bool

def validate_chemistry(state: PreservationState):
    # Simulate chemical safety check for fixatives like formalin
    print(f'Validating chemical safety for {state["specimen_id"]}')
    return {"chemical_safety_verified": True}

def verify_sterility(state: PreservationState):
    # Simulate biological integrity check
    print(f'Verifying sterility for {state["specimen_id"]}')
    return {"is_sterile": True}

graph_builder = StateGraph(PreservationState)
graph_builder.add_node("validate_chemistry", validate_chemistry)
graph_builder.add_node("verify_sterility", verify_sterility)
graph_builder.set_entry_point("validate_chemistry")
graph_builder.add_edge("validate_chemistry", "verify_sterility")
graph_builder.add_edge("verify_sterility", END)
graph = graph_builder.compile()