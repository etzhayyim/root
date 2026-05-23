from typing import TypedDict
from langgraph.graph import StateGraph, END

class CarboplatinState(TypedDict):
    purity: float
    temp_log: list
    is_sterile: bool

def validate_purity(state: CarboplatinState):
    return {"is_valid": state["purity"] >= 0.99}

def check_cold_chain(state: CarboplatinState):
    return {"cold_chain_ok": all(t < 25 for t in state["temp_log"])}

graph = StateGraph(CarboplatinState)
graph.add_node("validate_purity", validate_purity)
graph.add_node("check_cold_chain", check_cold_chain)
graph.set_entry_point("validate_purity")
graph.add_edge("validate_purity", "check_cold_chain")
graph.add_edge("check_cold_chain", END)
graph = graph.compile()
