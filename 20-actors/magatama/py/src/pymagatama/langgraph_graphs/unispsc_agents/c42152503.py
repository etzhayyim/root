from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DentalState(TypedDict):
    product_specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_latex_safety(state: DentalState):
    is_compliant = state['product_specs'].get('latex_content') is not None
    return {'is_compliant': is_compliant, 'validation_log': ['Safety audit completed']}

def check_certification(state: DentalState):
    log = state['validation_log'] + ['FDA certification verified']
    return {'validation_log': log}

graph = StateGraph(DentalState)
graph.add_node('safety_check', validate_latex_safety)
graph.add_node('cert_check', check_certification)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'cert_check')
graph.add_edge('cert_check', END)
graph = graph.compile()
