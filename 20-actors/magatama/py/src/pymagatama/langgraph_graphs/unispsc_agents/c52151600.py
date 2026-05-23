from typing import TypedDict
from langgraph.graph import StateGraph, END

class KitchenwareState(TypedDict):
    item_name: str
    safety_compliant: bool
    inspection_passed: bool

def validate_materials(state: KitchenwareState):
    print(f'Validating food safety standards for: {state["item_name"]}')
    return {"safety_compliant": True}

def perform_inspection(state: KitchenwareState):
    print('Executing QC check on physical utility.')
    return {"inspection_passed": True}

graph = StateGraph(KitchenwareState)
graph.add_node("validate", validate_materials)
graph.add_node("inspect", perform_inspection)
graph.add_edge("validate", "inspect")
graph.add_edge("inspect", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()
