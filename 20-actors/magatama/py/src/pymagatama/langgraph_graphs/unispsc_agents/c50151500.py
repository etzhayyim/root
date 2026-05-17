from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class OilProcurementState(TypedDict):
    oil_type: str
    quality_metrics: dict
    approved: bool

def validate_quality(state: OilProcurementState):
    # Business logic for oil quality check
    acid_val = state['quality_metrics'].get('acid_value', 10)
    state['approved'] = acid_val < 2.0
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(OilProcurementState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()