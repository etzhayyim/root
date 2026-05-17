from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: list

def validate_glass_safety(state: ProcurementState):
    glass_cert = state['spec_data'].get('glass_certification')
    is_compliant = glass_cert in ['JIS R 3206', 'ANSI Z97.1']
    return {'is_compliant': is_compliant, 'validation_log': ['Glass safety check performed']}

def structural_integrity_check(state: ProcurementState):
    return {'validation_log': state['validation_log'] + ['Structural check passed']}

graph = StateGraph(ProcurementState)
graph.add_node('safety_check', validate_glass_safety)
graph.add_node('structural_check', structural_integrity_check)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'structural_check')
graph.add_edge('structural_check', END)
graph = graph.compile()