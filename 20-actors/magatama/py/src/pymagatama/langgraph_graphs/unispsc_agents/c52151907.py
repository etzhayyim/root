from typing import TypedDict
from langgraph.graph import StateGraph, END

class BakingMoldState(TypedDict):
    material: str
    max_temp: int
    cert_passed: bool

def validate_material(state: BakingMoldState):
    print(f'Validating material: {state["material"]}')
    return {"cert_passed": state["material"] in ["silicone", "metal", "glass"]}

def check_temp(state: BakingMoldState):
    return {"cert_passed": state["max_temp"] >= 200}

graph = StateGraph(BakingMoldState)
graph.add_node("material_check", validate_material)
graph.add_node("temp_check", check_temp)
graph.add_edge("material_check", "temp_check")
graph.add_edge("temp_check", END)
graph.set_entry_point("material_check")
graph = graph.compile()
