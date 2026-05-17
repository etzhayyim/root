from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LicenseState(TypedDict):
    license_sku: str
    compliance_status: str
    optimization_report: dict

def validate_sku(state: LicenseState):
    state['compliance_status'] = 'VALIDATED' if state['license_sku'] else 'INVALID'
    return state

def generate_optimization(state: LicenseState):
    state['optimization_report'] = {'usage_efficiency': '85%', 'saving_potential': 'high'}
    return state

graph = StateGraph(LicenseState)
graph.add_node('validate', validate_sku)
graph.add_node('optimize', generate_optimization)
graph.add_edge('validate', 'optimize')
graph.add_edge('optimize', END)
graph.set_entry_point('validate')
graph = graph.compile()