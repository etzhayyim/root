from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CompressorState(TypedDict):
    spec_sheet: dict
    compliance_validated: bool
    approved: bool

def validate_iso_standards(state: CompressorState):
    standards = state['spec_sheet'].get('certifications', [])
    valid = 'ISO 13485' in standards and 'ISO 8573-1' in standards
    return {'compliance_validated': valid}

def approval_node(state: CompressorState):
    return {'approved': state['compliance_validated']}

graph = StateGraph(CompressorState)
graph.add_node('validate', validate_iso_standards)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()