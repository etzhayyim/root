from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    part_id: str
    spec_compliance: bool
    validation_log: Annotated[Sequence[str], operator.add]

def validate_specs(state: RobotState):
    log = [f"Validating specs for {state['part_id']}"]
    return {"spec_compliance": True, "validation_log": log}

def safety_check(state: RobotState):
    log = ["Running dual-use export control screening"]
    return {"validation_log": log}

graph = StateGraph(RobotState)
graph.add_node("validate", validate_specs)
graph.add_node("safety", safety_check)
graph.add_edge("validate", "safety")
graph.add_edge("safety", END)
graph.set_entry_point("validate")
graph = graph.compile()
