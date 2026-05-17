from typing import TypedDict
from langgraph.graph import StateGraph, END

class AVPlayerState(TypedDict):
    model_number: str
    region_compliance: bool
    is_tested: bool

def validate_specs(state: AVPlayerState):
    print(f"Validating player: {state['model_number']}")
    return {"region_compliance": True}

def perform_qa(state: AVPlayerState):
    print("Running functional playback test...")
    return {"is_tested": True}

graph = StateGraph(AVPlayerState)
graph.add_node("validate", validate_specs)
graph.add_node("qa", perform_qa)
graph.add_edge("validate", "qa")
graph.add_edge("qa", END)
graph.set_entry_point("validate")
graph = graph.compile()