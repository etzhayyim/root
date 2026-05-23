from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    part_id: str
    inspection_passed: bool
    validation_log: list

def validate_dimensions(state: ProcessingState):
    print(f"Validating dimensions for {state['part_id']}")
    return {"validation_log": ["Dimensions verified against CAD"]}

def check_bonding_integrity(state: ProcessingState):
    print(f"Checking bonding integrity for {state['part_id']}")
    return {"inspection_passed": True}

graph = StateGraph(ProcessingState)
graph.add_node("dimension_check", validate_dimensions)
graph.add_node("bonding_test", check_bonding_integrity)
graph.set_entry_point("dimension_check")
graph.add_edge("dimension_check", "bonding_test")
graph.add_edge("bonding_test", END)
graph = graph.compile()
