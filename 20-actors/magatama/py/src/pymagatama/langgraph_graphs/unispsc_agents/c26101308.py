from typing import TypedDict
from langgraph.graph import StateGraph, END

class MotorState(TypedDict):
    specs: dict
    validated: bool

def validate_motor_specs(state: MotorState):
    s = state['specs']
    valid = all([s.get('voltage', 0) in [100, 200], s.get('power', 0) > 0])
    return {"validated": valid}

def route_verification(state: MotorState):
    return "validated" if state['validated'] else END

graph = StateGraph(MotorState)
graph.add_node("validate", validate_motor_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph.compile()