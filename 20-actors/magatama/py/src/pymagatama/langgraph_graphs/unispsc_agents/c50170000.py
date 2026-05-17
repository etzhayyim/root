from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SeasoningState(TypedDict):
    product_name: str
    safety_certs: List[str]
    compliance_passed: bool

def validate_certification(state: SeasoningState):
    required = ['HACCP', 'ISO22000']
    passed = all(cert in state['safety_certs'] for cert in required)
    return {'compliance_passed': passed}

def approval_check(state: SeasoningState):
    return 'approved' if state['compliance_passed'] else 'rejected'

graph = StateGraph(SeasoningState)
graph.add_node('validate', validate_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()