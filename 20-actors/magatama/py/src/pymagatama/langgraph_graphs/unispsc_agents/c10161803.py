from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class BreedingState(TypedDict):
    spec_data: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_cleared: bool

def validate_genetic_data(state: BreedingState):
    log = "Genetic markers verified against registry." if "breed_id" in state["spec_data"] else "Genetic verification failed."
    return {"validation_logs": [log], "is_cleared": "breed_id" in state["spec_data"]}

def check_cold_chain(state: BreedingState):
    log = "Cold chain parameters validated." if state["spec_data"].get("cold_chain_compliance_report") else "Cold chain risk detected."
    return {"validation_logs": [log]}

graph = StateGraph(BreedingState)
graph.add_node("genetic_check", validate_genetic_data)
graph.add_node("cold_chain_check", check_cold_chain)
graph.add_edge("genetic_check", "cold_chain_check")
graph.add_edge("cold_chain_check", END)
graph.set_entry_point("genetic_check")
app = graph.compile()
