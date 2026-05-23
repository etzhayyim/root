from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class EmorfazoneState(TypedDict):
    purity: float
    gmp_certified: bool
    validation_logs: List[str]

def validate_purity(state: EmorfazoneState):
    log = 'Purity check passed' if state['purity'] >= 99.0 else 'Purity check failed'
    return {'validation_logs': [log]}

def check_compliance(state: EmorfazoneState):
    status = 'GMP Verified' if state['gmp_certified'] else 'GMP Missing'
    return {'validation_logs': state['validation_logs'] + [status]}

graph = StateGraph(EmorfazoneState)
graph.add_node('purity_check', validate_purity)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('purity_check')
graph.add_edge('purity_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()
