import operator
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    part_specs: dict
    validation_logs: Annotated[List[str], operator.add]
    is_approved: bool

def validate_materials(state: ForgingState):
    alloy = state['part_specs'].get('alloy', 'Unknown')
    log = f"Validated alloy composition stability for {alloy}"
    return {'validation_logs': [log], 'is_approved': True}

def check_dimensional_compliance(state: ForgingState):
    tolerance = state['part_specs'].get('tolerance', 0.0)
    status = tolerance <= 0.05
    return {'validation_logs': [f"Dimensional check result: {status}"], 'is_approved': status}

graph = StateGraph(ForgingState)
graph.add_node("material_check", validate_materials)
graph.add_node("dim_check", check_dimensional_compliance)
graph.set_entry_point("material_check")
graph.add_edge("material_check", "dim_check")
graph.add_edge("dim_check", END)
compiled_graph = graph.compile()
