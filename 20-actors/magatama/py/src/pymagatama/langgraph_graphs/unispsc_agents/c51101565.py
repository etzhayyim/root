from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    batch_id: str
    quality_passed: bool
    compliance_checks: List[str]

def validate_batch(state: PharmaState) -> PharmaState:
    # Logic to verify GMP and batch compliance
    state['quality_passed'] = True
    state['compliance_checks'].append('GMP_VALIDATED')
    return state

def check_storage(state: PharmaState) -> PharmaState:
    # Logic to monitor storage environment
    state['compliance_checks'].append('STORAGE_MONITORED')
    return state

def route_by_quality(state: PharmaState):
    return 'process' if state['quality_passed'] else END

graph = StateGraph(PharmaState)
graph.add_node('validate', validate_batch)
graph.add_node('process', check_storage)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_quality)
graph.add_edge('process', END)
graph = graph.compile()
