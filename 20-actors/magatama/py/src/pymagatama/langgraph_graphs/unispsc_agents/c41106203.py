from langgraph.graph import StateGraph, END
from typing import TypedDict

class KitState(TypedDict):
    kit_id: str
    validation_status: bool
    temp_log: float

def validate_cold_chain(state: KitState):
    return {"validation_status": state["temp_log"] <= -80.0}

def process_batch(state: KitState):
    print(f"Processing transformation kit: {state['kit_id']}")
    return {"validation_status": True}

graph = StateGraph(KitState)
graph.add_node("validate", validate_cold_chain)
graph.add_node("process", process_batch)
graph.add_edge("validate", "process")
graph.add_edge("process", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()