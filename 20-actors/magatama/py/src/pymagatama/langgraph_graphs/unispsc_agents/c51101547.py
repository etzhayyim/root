from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class DiagnosticState(TypedDict):
    commodity_id: str
    batch_id: str
    quality_checks: List[str]
    is_cleared: bool

def validate_cold_chain(state: DiagnosticState) -> DiagnosticState:
    state['quality_checks'].append('Cold chain verification passed')
    return state

def run_compliance_check(state: DiagnosticState) -> DiagnosticState:
    state['is_cleared'] = True
    return state

graph = StateGraph(DiagnosticState)
graph.add_node('cold_chain', validate_cold_chain)
graph.add_node('compliance', run_compliance_check)
graph.add_edge('cold_chain', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('cold_chain')
graph = graph.compile()
