from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssetTagState(TypedDict):
    specification: dict
    validation_report: str

def validate_materials(state: AssetTagState):
    check = state['specification'].get('material', 'plastic')
    return {"validation_report": f"Validated material: {check}"}

def check_durability(state: AssetTagState):
    return {"validation_report": state['validation_report'] + " - Durability standard met."}

graph = StateGraph(AssetTagState)
graph.add_node("validate_materials", validate_materials)
graph.add_node("check_durability", check_durability)
graph.set_entry_point("validate_materials")
graph.add_edge("validate_materials", "check_durability")
graph.add_edge("check_durability", END)
graph = graph.compile()