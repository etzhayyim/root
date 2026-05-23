from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ITState(TypedDict):
    commodity_id: str
    spec_requirements: list[str]
    validation_logs: Annotated[list[str], operator.add]
    status: str

def validate_it_spec(state: ITState) -> ITState:
    logs = [f"Validating specs for {state['commodity_id']}"]
    if not state['spec_requirements']:
        logs.append("Missing critical spec requirements")
    return {**state, "validation_logs": logs, "status": "validated"}

def route_to_procurement(state: ITState) -> str:
    return "procure"

builder = StateGraph(ITState)
builder.add_node("validate", validate_it_spec)
builder.add_edge("validate", END)
builder.set_entry_point("validate")
graph = builder.compile()
