from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class KitchenScaleState(TypedDict):
    spec: dict
    validation_log: List[str]
    is_compliant: bool
def validate_specs(state: KitchenScaleState):
    log = []
    compliant = True
    if state['spec'].get('accuracy') is None:
        log.append("Missing accuracy specification")
        compliant = False
    return {"validation_log": log, "is_compliant": compliant}
def finalize_procurement(state: KitchenScaleState):
    return {"validation_log": state['validation_log'] + ["Finalized"]}
graph = StateGraph(KitchenScaleState)
graph.add_node("validate", validate_specs)
graph.add_node("finalize", finalize_procurement)
graph.set_entry_point("validate")
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
graph = graph.compile()
