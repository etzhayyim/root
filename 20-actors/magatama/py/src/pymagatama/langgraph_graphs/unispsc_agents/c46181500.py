from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SafetyApparelState(TypedDict):
    item_name: str
    standards: List[str]
    is_compliant: bool

def validate_certification(state: SafetyApparelState):
    required_standards = ['EN ISO 20471', 'ANSI/ISEA 107']
    state['is_compliant'] = any(s in state['standards'] for s in required_standards)
    return state

workflow = StateGraph(SafetyApparelState)
workflow.add_node('cert_validation', validate_certification)
workflow.set_entry_point('cert_validation')
workflow.add_edge('cert_validation', END)
graph = workflow.compile()