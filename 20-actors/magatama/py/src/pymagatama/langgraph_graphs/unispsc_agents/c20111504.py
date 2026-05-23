from typing import TypedDict, Annotated, List, Any
from langgraph.graph import StateGraph, END

class GearProcurementState(TypedDict):
    gear_specs: dict
    validation_results: List[str]
    is_approved: bool

def validate_gear_specs(state: GearProcurementState) -> GearProcurementState:
    specs = state['gear_specs']
    results = []
    if 'tolerance_grade' not in specs: results.append('Missing tolerance_grade')
    if 'material_specification' not in specs: results.append('Missing material_specification')
    return {**state, 'validation_results': results, 'is_approved': len(results) == 0}

def route_by_validation(state: GearProcurementState) -> str:
    return 'approved' if state['is_approved'] else 'rejected'

builder = StateGraph(GearProcurementState)
builder.add_node('validate', validate_gear_specs)
builder.set_entry_point('validate')
builder.add_conditional_edges('validate', route_by_validation, {'approved': END, 'rejected': END})
graph = builder.compile()
