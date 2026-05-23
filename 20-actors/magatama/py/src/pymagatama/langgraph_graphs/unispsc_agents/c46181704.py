from typing import TypedDict
from langgraph.graph import StateGraph, END

class HelmetState(TypedDict):
    compliance_data: dict
    approved: bool

def validate_compliance(state: HelmetState):
    standards = state['compliance_data'].get('standard', '')
    return {'approved': any(s in standards for s in ['ANSI', 'JIS', 'EN397'])}

workflow = StateGraph(HelmetState)
workflow.add_node('validate', validate_compliance)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
