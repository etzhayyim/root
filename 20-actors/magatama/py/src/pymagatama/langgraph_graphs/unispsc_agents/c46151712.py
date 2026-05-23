from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForensicState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_airflow(state: ForensicState):
    airflow = state['spec_data'].get('airflow', 0)
    valid = 0.4 <= airflow <= 0.6
    return {'validation_results': [f'Airflow valid: {valid}'], 'is_compliant': valid}

def check_certifications(state: ForensicState):
    certs = state['spec_data'].get('certs', [])
    valid = 'HEPA_H14' in certs
    return {'validation_results': state['validation_results'] + [f'Certs valid: {valid}'], 'is_compliant': state['is_compliant'] and valid}

graph = StateGraph(ForensicState)
graph.add_node('airflow_check', validate_airflow)
graph.add_node('cert_check', check_certifications)
graph.set_entry_point('airflow_check')
graph.add_edge('airflow_check', 'cert_check')
graph.add_edge('cert_check', END)
graph = graph.compile()
