from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    purity_level: float
    inspection_passed: bool
    compliance_logs: List[str]

def validate_purity(state: CatalystState):
    state['inspection_passed'] = state['purity_level'] >= 99.9
    return state

def log_compliance(state: CatalystState):
    if state['inspection_passed']:
        state['compliance_logs'].append('Compliance Verified: Standard ISO-1214 met.')
    return state

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', log_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
compiled_graph = graph.compile()