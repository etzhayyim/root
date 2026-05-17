from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FinishingSpecState(TypedDict):
    material_type: str
    spec_data: dict
    is_compliant: bool
    validation_log: List[str]

def validate_materials(state: FinishingSpecState):
    log = []
    compliant = True
    if 'VOC' not in state['spec_data']:
        log.append("Missing VOC emission data")
        compliant = False
    return {"validation_log": log, "is_compliant": compliant}

def approval_step(state: FinishingSpecState):
    print(f"Processing finishing material: {state['material_type']}")
    return {"validation_log": state['validation_log'] + ["Approved for procurement"]}

graph = StateGraph(FinishingSpecState)
graph.add_node("validation", validate_materials)
graph.add_node("approval", approval_step)
graph.set_entry_point("validation")
graph.add_edge("validation", "approval")
graph.add_edge("approval", END)
graph = graph.compile()