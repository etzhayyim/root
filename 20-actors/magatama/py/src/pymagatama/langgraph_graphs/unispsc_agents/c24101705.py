from typing import TypedDict
from langgraph.graph import StateGraph, END

class ConveyorState(TypedDict):
    specs: dict
    validated: bool
    error_log: list

def validate_specs(state: ConveyorState):
    required = ['material_grade', 'pitch', 'diameter']
    valid = all(k in state['specs'] for k in required)
    return {"validated": valid}

def route_by_spec(state: ConveyorState):
    return "validated" if state['validated'] else "error"

graph = StateGraph(ConveyorState)
graph.add_node("validation", validate_specs)
graph.set_entry_point("validation")
graph.add_edge("validation", END)
graph.compile()