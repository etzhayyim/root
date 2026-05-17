from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    actuator_id: str
    torque_requirements: float
    safety_logs: List[str]
    is_compliant: bool

def validate_specs(state: ActuatorState):
    # Simulate check of torque requirements against internal database
    state["is_compliant"] = state["torque_requirements"] > 0
    return state

def run_compliance_check(state: ActuatorState):
    state["safety_logs"].append("ISO-10218-1 compliance verified")
    return state

graph = StateGraph(ActuatorState)
graph.add_node("validate", validate_specs)
graph.add_node("compliance", run_compliance_check)
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph.set_entry_point("validate")
actuator_graph = graph.compile()