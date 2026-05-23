from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    catalyst_id: str
    purity_level: float
    compliance_checks: Annotated[Sequence[str], operator.add]
    status: str

def validate_purity(state: CatalystState):
    is_pure = state['purity_level'] >= 0.99
    return {'compliance_checks': ['purity_verified'] if is_pure else ['purity_failed']}

def perform_compliance_audit(state: CatalystState):
    return {'status': 'AUDITED' if 'purity_verified' in state['compliance_checks'] else 'REJECTED'}

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_purity)
graph.add_node('audit', perform_compliance_audit)
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
graph.set_entry_point('validate')
graph = graph.compile()
