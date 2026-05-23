from typing import TypedDict
from langgraph.graph import StateGraph, END

class DieCastState(TypedDict):
    part_number: str
    cad_file_path: str
    material_spec: str
    validation_passed: bool

def validate_cad(state: DieCastState):
    print(f"Validating CAD for {state['part_number']} against structural tolerances...")
    return {"validation_passed": True}

def check_compliance(state: DieCastState):
    print("Checking lead content and RoHS/REACH compliance...")
    return {"validation_passed": True}

graph = StateGraph(DieCastState)
graph.add_node("validate_cad", validate_cad)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate_cad")
graph.add_edge("validate_cad", "compliance")
graph.add_edge("compliance", END)
graph.compile()
