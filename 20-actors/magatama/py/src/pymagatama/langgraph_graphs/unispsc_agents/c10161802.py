from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SeedIngestState(TypedDict):
    seed_id: str
    germination_rate: float
    quarantine_status: bool
    validation_log: List[str]

def validate_germination(state: SeedIngestState) -> SeedIngestState:
    is_valid = state['germination_rate'] >= 85.0
    state['validation_log'].append(f'Germination check: {is_valid}')
    return state

def check_quarantine(state: SeedIngestState) -> SeedIngestState:
    state['validation_log'].append(f'Quarantine cleared: {state['quarantine_status']}')
    return state

graph = StateGraph(SeedIngestState)
graph.add_node('validate_germination', validate_germination)
graph.add_node('check_quarantine', check_quarantine)
graph.set_entry_point('validate_germination')
graph.add_edge('validate_germination', 'check_quarantine')
graph.add_edge('check_quarantine', END)

graph = graph.compile()