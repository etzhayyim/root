from typing import TypedDict
from langgraph.graph import StateGraph, END

class FastenerState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: FastenerState):
    # Simulate CAD and tensile validation
    state['approved'] = 'material' in state['specs'] and 'thread_pitch' in state['specs']
    return state

def output_result(state: FastenerState):
    print(f"Procurement status: {state['approved']}")
    return state

graph = StateGraph(FastenerState)
graph.add_node("validate", validate_specs)
graph.add_node("finalize", output_result)
graph.set_entry_point("validate")
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
graph = graph.compile()
