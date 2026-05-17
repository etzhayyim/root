from typing import TypedDict
from langgraph.graph import StateGraph, END

class CatheterState(TypedDict):
    sterility_check: bool
    compliance_docs: list
    validation_status: str

def validate_compliance(state: CatheterState):
    if 'ISO_13485' in state['compliance_docs']:
        return {'validation_status': 'compliant'}
    return {'validation_status': 'non_compliant'}

def perform_sterility_check(state: CatheterState):
    return {'sterility_check': True}

graph = StateGraph(CatheterState)
graph.add_node('compliance', validate_compliance)
graph.add_node('sterility', perform_sterility_check)
graph.set_entry_point('sterility')
graph.add_edge('sterility', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()