from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CarbonFiberState(TypedDict):
    material_id: str
    spec_data: dict
    validation_score: float
    export_required: bool

def validate_material_specs(state: CarbonFiberState) -> CarbonFiberState:
    # Logic to validate fiber strength against aerospace standards
    state['validation_score'] = 0.95
    return state

def check_dual_use(state: CarbonFiberState) -> CarbonFiberState:
    # Logic to determine export control necessity based on tensile properties
    state['export_required'] = state['spec_data'].get('tensile_strength_mpa', 0) > 5000
    return state

workflow = StateGraph(CarbonFiberState)
workflow.add_node('validate', validate_material_specs)
workflow.add_node('export_check', check_dual_use)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'export_check')
workflow.add_edge('export_check', END)
graph = workflow.compile()