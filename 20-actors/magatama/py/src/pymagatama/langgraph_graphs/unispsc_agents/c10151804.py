from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SeedState(TypedDict):
    seed_id: str
    quarantine_status: bool
    germination_result: float
    inspection_passed: bool

def validate_quarantine(state: SeedState) -> SeedState:
    # Simulate strict regulatory check for agricultural seeds
    state['quarantine_status'] = True
    return state

def run_quality_check(state: SeedState) -> SeedState:
    # Simulate laboratory analysis for seed viability
    state['inspection_passed'] = state['germination_result'] > 0.85
    return state

graph = StateGraph(SeedState)
graph.add_node('validate_quarantine', validate_quarantine)
graph.add_node('run_quality_check', run_quality_check)
graph.set_entry_point('validate_quarantine')
graph.add_edge('validate_quarantine', 'run_quality_check')
graph.add_edge('run_quality_check', END)
graph = graph.compile()