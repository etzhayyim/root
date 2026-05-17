from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class NuclearMaterialState(TypedDict):
    material_id: str
    purity_cert: str
    is_cleared: bool
    log: List[str]

def validate_purity(state: NuclearMaterialState):
    # Simulate regulatory validation logic
    is_pure = len(state['purity_cert']) > 10
    return {"is_cleared": is_pure, "log": ["Purity check performed"]}

def security_clearance(state: NuclearMaterialState):
    # Check for export controls
    return {"is_cleared": state['is_cleared'] and True, "log": state['log'] + ["Security clearance passed"]}

graph = StateGraph(NuclearMaterialState)
graph.add_node("validate", validate_purity)
graph.add_node("security", security_clearance)
graph.add_edge("validate", "security")
graph.add_edge("security", END)
graph.set_entry_point("validate")
app = graph.compile()