from typing import TypedDict
from langgraph.graph import StateGraph, END

class UniformState(TypedDict):
    spec_data: dict
    approved: bool
    validation_log: list

def validate_specs(state: UniformState):
    log = []
    if 'material_composition' not in state['spec_data']:
        log.append("Missing mandatory material specs")
    return {"validation_log": log, "approved": len(log) == 0}

def security_review(state: UniformState):
    # Simulate security clearance lookup
    return {"approved": state['approved'] and True}

graph = StateGraph(UniformState)
graph.add_node("validate", validate_specs)
graph.add_node("security", security_review)
graph.set_entry_point("validate")
graph.add_edge("validate", "security")
graph.add_edge("security", END)
graph = graph.compile()
