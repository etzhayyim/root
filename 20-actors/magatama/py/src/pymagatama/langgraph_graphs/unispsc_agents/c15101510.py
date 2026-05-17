from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class MaterialProcessingState(TypedDict):
    material_id: str
    spec_compliance: bool
    validation_log: Annotated[Sequence[str], operator.add]
    process_status: str

def validate_material_specs(state: MaterialProcessingState):
    log = [f"Validating material {state['material_id']} specs."]
    return {"spec_compliance": True, "validation_log": log, "process_status": "Validated"}

def conduct_stress_test(state: MaterialProcessingState):
    log = ["Performing tensile and thermal stress testing."]
    return {"process_status": "StressTested", "validation_log": log}

def finalize_batch(state: MaterialProcessingState):
    return {"process_status": "ReadyForDispatch"}

graph = StateGraph(MaterialProcessingState)
graph.add_node("validate", validate_material_specs)
graph.add_node("test", conduct_stress_test)
graph.add_node("finalize", finalize_batch)
graph.add_edge("validate", "test")
graph.add_edge("test", "finalize")
graph.add_edge("finalize", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()