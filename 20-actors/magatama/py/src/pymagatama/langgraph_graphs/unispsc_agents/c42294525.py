from typing import TypedDict
from langgraph.graph import StateGraph, END

class OphthalmicState(TypedDict):
    instrument_list: list
    cert_check: bool
    approved: bool

def validate_instruments(state: OphthalmicState):
    # Business logic for instrument set validation
    valid = all(['iso_compliant' in item for item in state['instrument_list']])
    return {"cert_check": valid}

def approval_step(state: OphthalmicState):
    return {"approved": state['cert_check']}

graph = StateGraph(OphthalmicState)
graph.add_node("validate", validate_instruments)
graph.add_node("approve", approval_step)
graph.add_edge("validate", "approve")
graph.add_edge("approve", END)
graph.set_entry_point("validate")
graph = graph.compile()
