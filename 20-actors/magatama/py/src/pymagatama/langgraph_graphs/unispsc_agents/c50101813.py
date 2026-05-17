from typing import TypedDict
from langgraph.graph import StateGraph, END

class TangerineState(TypedDict):
    temp_range: str
    quality_check: bool
    phytosanitary_doc: bool

def validate_cold_chain(state: TangerineState):
    return {"quality_check": 2.0 <= float(state['temp_range'].split('-')[0]) <= 8.0}

def verify_certs(state: TangerineState):
    return {"phytosanitary_doc": True}

graph = StateGraph(TangerineState)
graph.add_node("validate", validate_cold_chain)
graph.add_node("certs", verify_certs)
graph.add_edge("validate", "certs")
graph.add_edge("certs", END)
graph.set_entry_point("validate")
graph = graph.compile()