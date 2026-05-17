from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlourProcurementState(TypedDict):
    moisture_level: float
    purity_certified: bool
    approved: bool

def validate_quality(state: FlourProcurementState):
    # Business logic for flour quality check
    is_dry = state['moisture_level'] < 14.0
    state['approved'] = is_dry and state['purity_certified']
    return state

workflow = StateGraph(FlourProcurementState)
workflow.add_node('quality_check', validate_quality)
workflow.set_entry_point('quality_check')
workflow.add_edge('quality_check', END)
graph = workflow.compile()