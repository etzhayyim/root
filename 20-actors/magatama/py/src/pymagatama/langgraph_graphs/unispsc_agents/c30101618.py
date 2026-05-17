from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RubberState(TypedDict):
    material_type: str
    hardness: int
    is_compliant: bool
    validation_log: List[str]

def validate_rubber_specs(state: RubberState):
    log = state.get('validation_log', [])
    compliant = state['hardness'] > 40
    log.append(f'Hardness check: {"passed" if compliant else "failed"}')
    return {"is_compliant": compliant, "validation_log": log}

graph = StateGraph(RubberState)
graph.add_node("validate", validate_rubber_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()