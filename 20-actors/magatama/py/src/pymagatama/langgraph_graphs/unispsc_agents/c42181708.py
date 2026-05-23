from typing import TypedDict
from langgraph.graph import StateGraph, END

class EKGState(TypedDict):
    electrode_type: str
    compliance_docs: list
    validation_passed: bool

def validate_compliance(state: EKGState):
    required = ['FDA', 'ISO_13485']
    passed = all(doc in state['compliance_docs'] for doc in required)
    return {'validation_passed': passed}

def route_by_validation(state: EKGState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(EKGState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': 'process', '__end__': END})
graph.add_node('process', lambda s: s)
graph.add_edge('process', END)
graph = graph.compile()
