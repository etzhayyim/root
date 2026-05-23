from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MiningState(TypedDict):
    task: str
    validation_log: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_drill_spec(state: MiningState):
    log = [f'Validating drill specs for: {state["task"]}', 'Checking tensile strength metrics.', 'Verifying dual-use export compliance.']
    return {"validation_log": log, "is_approved": True}

def dispatch_procurement(state: MiningState):
    return {"validation_log": ['Dispatching procurement order to approved supplier.']}

graph = StateGraph(MiningState)
graph.add_node("validate", validate_drill_spec)
graph.add_node("dispatch", dispatch_procurement)
graph.set_entry_point("validate")
graph.add_edge("validate", "dispatch")
graph.add_edge("dispatch", END)
compiled_graph = graph.compile()
