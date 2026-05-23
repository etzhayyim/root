from typing import TypedDict
from langgraph.graph import StateGraph, END

class OstomyState(TypedDict):
    product_id: str
    compliance_docs: list[str]
    validation_passed: bool

def validate_compliance(state: OstomyState):
    required = {'ISO_10993', 'FDA_clearance'}
    state['validation_passed'] = all(doc in state['compliance_docs'] for doc in required)
    return state

def route_by_validation(state: OstomyState):
    return 'process' if state['validation_passed'] else 'reject'

graph = StateGraph(OstomyState)
graph.add_node('validate', validate_compliance)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
