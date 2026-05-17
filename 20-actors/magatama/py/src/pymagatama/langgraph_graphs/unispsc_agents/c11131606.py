from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MaterialState(TypedDict):
    material_code: str
    purity_level: float
    safety_clearance: bool
    inspection_log: Annotated[Sequence[str], operator.add]

def validate_material_spec(state: MaterialState) -> dict:
    # Logic to verify material specifications
    is_safe = state['purity_level'] > 0.99
    return {'safety_clearance': is_safe, 'inspection_log': ['Spec validation completed']}

def perform_export_check(state: MaterialState) -> dict:
    # Logic for dual-use export control
    return {'inspection_log': ['Dual-use control screening passed']}

def finalize_ingest(state: MaterialState) -> dict:
    return {'inspection_log': ['Material ingestion finalized']}

workflow = StateGraph(MaterialState)
workflow.add_node('validate', validate_material_spec)
workflow.add_node('export_control', perform_export_check)
workflow.add_node('finalize', finalize_ingest)

workflow.set_entry_point('validate')
workflow.add_edge('validate', 'export_control')
workflow.add_edge('export_control', 'finalize')
workflow.add_edge('finalize', END)

graph = workflow.compile()