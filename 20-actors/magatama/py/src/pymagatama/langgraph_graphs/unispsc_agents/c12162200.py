from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AdditiveState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_checks: List[str]
    approved: bool

def validate_purity(state: AdditiveState):
    # Simulate purity check for industrial catalysts
    is_pure = state['purity_level'] >= 99.5
    return {'compliance_checks': state['compliance_checks'] + ['purity_verified'], 'approved': is_pure}

def safety_audit(state: AdditiveState):
    # Simulate dangerous goods safety audit
    return {'compliance_checks': state['compliance_checks'] + ['safety_audit_passed'], 'approved': state['approved']}

graph = StateGraph(AdditiveState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('safety_audit', safety_audit)
graph.add_edge('validate_purity', 'safety_audit')
graph.add_edge('safety_audit', END)
graph.set_entry_point('validate_purity')
compiled_graph = graph.compile()