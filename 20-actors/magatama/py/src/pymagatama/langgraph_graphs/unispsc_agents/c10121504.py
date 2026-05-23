from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class GrainProcurementState(TypedDict):
    commodity_code: str
    quality_metrics: dict
    approved: bool
    history: Annotated[List[str], list.append]

def validate_grain_quality(state: GrainProcurementState):
    metrics = state.get('quality_metrics', {})
    is_valid = metrics.get('moisture', 0) < 14.0 and metrics.get('impurities', 0) < 1.0
    return {'approved': is_valid, 'history': ['Validated moisture and impurities']}

def update_procurement_log(state: GrainProcurementState):
    return {'history': ['Logged quality validation result']}

builder = StateGraph(GrainProcurementState)
builder.add_node('validate', validate_grain_quality)
builder.add_node('log', update_procurement_log)
builder.add_edge('validate', 'log')
builder.add_edge('log', END)
builder.set_entry_point('validate')
graph = builder.compile()
