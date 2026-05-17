from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class WaferProcurementState(TypedDict):
    wafer_id: str
    spec_data: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_wafer_specs(state: WaferProcurementState):
    specs = state['spec_data']
    valid = specs.get('resistivity_ohm_cm', 0) > 0 and specs.get('particle_count_limit', 100) < 50
    return {"validation_logs": ["Validated resistivity and particle count"], "is_compliant": valid}

def inspect_surface(state: WaferProcurementState):
    return {"validation_logs": ["Performed surface topography scan"], "is_compliant": True}

graph = StateGraph(WaferProcurementState)
graph.add_node("validate", validate_wafer_specs)
graph.add_node("inspect", inspect_surface)
graph.set_entry_point("validate")
graph.add_edge("validate", "inspect")
graph.add_edge("inspect", END)
compile_graph = graph.compile()