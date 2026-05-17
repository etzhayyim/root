from typing import TypedDict
from langgraph.graph import StateGraph, END

class LanguageCertState(TypedDict):
    cert_type: str
    validation_status: bool
    compliance_check: bool

def validate_cert_provider(state: LanguageCertState):
    print(f'Validating provider for: {state["cert_type"]}')
    return {'validation_status': True}

def check_compliance(state: LanguageCertState):
    print('Checking GDPR/Privacy compliance for student data')
    return {'compliance_check': True}

graph = StateGraph(LanguageCertState)
graph.add_node('validate', validate_cert_provider)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()