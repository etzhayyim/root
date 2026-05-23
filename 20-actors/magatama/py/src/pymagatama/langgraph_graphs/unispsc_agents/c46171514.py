from typing import TypedDict
from langgraph.graph import StateGraph, END

class SecurityChainState(TypedDict):
    spec: dict
    validated: bool
    compliance_report: str

def validate_tensile_strength(state: SecurityChainState):
    strength = state['spec'].get('tensile_strength', 0)
    state['validated'] = strength > 5000
    return state

def generate_compliance(state: SecurityChainState):
    state['compliance_report'] = 'Compliance Verified' if state['validated'] else 'Compliance Failed'
    return state

graph = StateGraph(SecurityChainState)
graph.add_node('validate', validate_tensile_strength)
graph.add_node('compliance', generate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
