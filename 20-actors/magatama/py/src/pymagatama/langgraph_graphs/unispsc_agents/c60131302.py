from typing import TypedDict
from langgraph.graph import StateGraph, END

class InstrumentState(TypedDict):
    instrument_type: str
    quality_check_passed: bool
    shipping_specs: dict

def validate_instrument(state: InstrumentState):
    print(f"Validating specifications for: {state['instrument_type']}")
    return {"quality_check_passed": True}

def route_shipping(state: InstrumentState):
    return "ship" if state['quality_check_passed'] else END

graph = StateGraph(InstrumentState)
graph.add_node("validate", validate_instrument)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph.compile()
