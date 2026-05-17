from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RibbonState(TypedDict):
    material_spec: str
    quality_tests: List[str]
    approved: bool

def validate_material(state: RibbonState):
    print(f"Validating synthetic structure: {state['material_spec']}")
    return {"approved": "synthetic" in state['material_spec'].lower()}

def finalize_order(state: RibbonState):
    return {"approved": True}

graph = StateGraph(RibbonState)
graph.add_node("validate", validate_material)
graph.add_node("finalize", finalize_order)
graph.set_entry_point("validate")
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
graph = graph.compile()