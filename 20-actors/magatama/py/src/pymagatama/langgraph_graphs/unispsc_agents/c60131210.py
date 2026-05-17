from typing import TypedDict
from langgraph.graph import StateGraph, END

class OcarinaState(TypedDict):
    material: str
    pitch_standard: str
    inspection_passed: bool

def validate_materials(state: OcarinaState):
    return {"inspection_passed": state["material"] in ["Ceramic", "Plastic", "Wood"]}

def check_pitch(state: OcarinaState):
    return {"inspection_passed": state["pitch_standard"] == "A=440Hz" and state["inspection_passed"]}

graph = StateGraph(OcarinaState)
graph.add_node("validate_materials", validate_materials)
graph.add_node("check_pitch", check_pitch)
graph.set_entry_point("validate_materials")
graph.add_edge("validate_materials", "check_pitch")
graph.add_edge("check_pitch", END)
compiled_graph = graph.compile()