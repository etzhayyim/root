from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    commodity_code: str
    quality_score: float
    quarantine_cleared: bool
    vendor_id: str
    steps_completed: List[str]

def check_quarantine(state: ProcurementState) -> ProcurementState:
    # Simulate quarantine validation logic
    state['quarantine_cleared'] = True
    state['steps_completed'].append('quarantine_check')
    return state

def assess_vendor(state: ProcurementState) -> ProcurementState:
    # Simulate vendor compliance check
    state['quality_score'] = 0.95
    state['steps_completed'].append('vendor_assessment')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('quarantine', check_quarantine)
graph.add_node('vendor', assess_vendor)
graph.add_edge('quarantine', 'vendor')
graph.add_edge('vendor', END)
graph.set_entry_point('quarantine')
graph = graph.compile()