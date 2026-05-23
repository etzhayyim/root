from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    drug_name: str
    purity_level: float
    temp_log: List[float]
    is_compliant: bool

def validate_compliance(state: PharmaState):
    compliant = state['purity_level'] >= 0.99 and all(2 <= t <= 8 for t in state['temp_log'])
    return {'is_compliant': compliant}

def check_certification(state: PharmaState):
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(PharmaState)
graph.add_node('validation', validate_compliance)
graph.add_node('cert_check', check_certification)
graph.add_edge('validation', 'cert_check')
graph.add_edge('cert_check', END)
graph.set_entry_point('validation')
compiled_graph = graph.compile()
