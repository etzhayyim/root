from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class CastForgeState(TypedDict):
    spec_data: dict
    validation_logs: List[str]
    is_approved: bool

def validate_materials(state: CastForgeState):
    log = f"Validating material grade: {state['spec_data'].get('material_grade')}"
    return {"validation_logs": [log], "is_approved": True}

def check_tolerances(state: CastForgeState):
    log = f"Checking dimensional tolerance: {state['spec_data'].get('dimensional_tolerance_mm')}mm"
    return {"validation_logs": [log], "is_approved": True}

graph = StateGraph(CastForgeState)
graph.add_node("validate_materials", validate_materials)
graph.add_node("check_tolerances", check_tolerances)
graph.set_entry_point("validate_materials")
graph.add_edge("validate_materials", "check_tolerances")
graph.add_edge("check_tolerances", END)
app = graph.compile()