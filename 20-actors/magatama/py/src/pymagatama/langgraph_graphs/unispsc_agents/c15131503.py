from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class TitaniumState(TypedDict):
    part_id: str
    material_spec: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_material(state: TitaniumState):
    log = f'Validating AMS spec for {state["part_id"]}'
    return {"validation_logs": [log], "is_approved": True}

def structural_integrity_check(state: TitaniumState):
    log = f'Running ultrasonic integrity check on {state["part_id"]}'
    return {"validation_logs": [log]}

graph = StateGraph(TitaniumState)
graph.add_node("validate", validate_material)
graph.add_node("integrity", structural_integrity_check)
graph.add_edge("validate", "integrity")
graph.add_edge("integrity", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()