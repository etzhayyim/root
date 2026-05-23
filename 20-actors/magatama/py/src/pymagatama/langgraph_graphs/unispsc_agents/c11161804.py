from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class CarbonFiberState(TypedDict):
    material_id: str
    spec_data: Dict[str, Any]
    validation_log: List[str]
    export_compliant: bool

def validate_specs(state: CarbonFiberState) -> CarbonFiberState:
    spec = state.get('spec_data', {})
    logs = state.get('validation_log', [])
    if spec.get('tensile_strength_mpa', 0) < 3000:
        logs.append('Validation Error: Insufficient tensile strength')
    state['validation_log'] = logs
    return state

def check_export_control(state: CarbonFiberState) -> CarbonFiberState:
    # High-performance carbon fiber is often dual-use
    state['export_compliant'] = state['spec_data'].get('elastic_modulus_gpa', 0) < 230
    return state

builder = StateGraph(CarbonFiberState)
builder.add_node('validate', validate_specs)
builder.add_node('export_check', check_export_control)
builder.set_entry_point('validate')
builder.add_edge('validate', 'export_check')
builder.add_edge('export_check', END)
graph = builder.compile()
