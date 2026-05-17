from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EsophagealScopeState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_report: str

def validate_biocompatibility(state: EsophagealScopeState):
    compliance = state['specs'].get('iso_10993', False)
    return {'is_compliant': compliance, 'validation_report': 'ISO 10993 check complete'}

def route_by_compliance(state: EsophagealScopeState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(EsophagealScopeState)
graph.add_node('validate', validate_biocompatibility)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()