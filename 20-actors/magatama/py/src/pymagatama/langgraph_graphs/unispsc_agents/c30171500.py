from typing import TypedDict
from langgraph.graph import StateGraph, END

class DoorState(TypedDict):
    specs: dict
    approved: bool

def validate_door_specs(state: DoorState):
    required = ['fire_rating', 'material']
    all_present = all(k in state['specs'] for k in required)
    return {'approved': all_present}

def final_check(state: DoorState):
    print(f"Procurement status: {state['approved']}")

graph = StateGraph(DoorState)
graph.add_node("validate", validate_door_specs)
graph.add_node("complete", final_check)
graph.set_entry_point("validate")
graph.add_edge("validate", "complete")
graph.add_edge("complete", END)
app = graph.compile()