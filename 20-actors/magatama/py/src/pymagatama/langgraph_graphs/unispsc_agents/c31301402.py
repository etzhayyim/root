from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    part_id: str
    material_certified: bool
    tolerance_checked: bool

def validate_specs(state: ForgingState) -> ForgingState:
    print(f'Validating specs for {state["part_id"]}')
    return {**state, "material_certified": True, "tolerance_checked": True}

def quality_control(state: ForgingState) -> ForgingState:
    print('Running surface finish analysis...')
    return state

graph = StateGraph(ForgingState)
graph.add_node("validate", validate_specs)
graph.add_node("qc", quality_control)
graph.set_entry_point("validate")
graph.add_edge("validate", "qc")
graph.add_edge("qc", END)
app = graph.compile()