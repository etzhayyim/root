from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SeedProcurementState(TypedDict):
    seed_code: str
    germination_rate: float
    quarantine_status: str
    approved: bool

def validate_purity(state: SeedProcurementState) -> SeedProcurementState:
    # Logic for purity validation
    state['approved'] = state['germination_rate'] > 0.85
    return state

def quarantine_check(state: SeedProcurementState) -> SeedProcurementState:
    # Logic for quarantine documentation check
    state['quarantine_status'] = 'CLEARED' if state.get('quarantine_status') == 'PASSED' else 'PENDING'
    return state

workflow = StateGraph(SeedProcurementState)
workflow.add_node('purity_check', validate_purity)
workflow.add_node('quarantine', quarantine_check)
workflow.set_entry_point('purity_check')
workflow.add_edge('purity_check', 'quarantine')
workflow.add_edge('quarantine', END)
graph = workflow.compile()
