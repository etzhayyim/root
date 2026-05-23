from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrainageState(TypedDict):
    device_id: str
    is_sterile: bool
    pressure_val: float
    approved: bool

def validate_sterilization(state: DrainageState):
    return {"is_sterile": True}

def check_pressure_rating(state: DrainageState):
    return {"approved": state["pressure_val"] > 0}

graph = StateGraph(DrainageState)
graph.add_node("validate_sterility", validate_sterilization)
graph.add_node("check_spec", check_pressure_rating)
graph.set_entry_point("validate_sterility")
graph.add_edge("validate_sterility", "check_spec")
graph.add_edge("check_spec", END)
graph = graph.compile()
