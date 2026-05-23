from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AutomationState(TypedDict):
    device_id: str
    specs: dict
    validation_passed: bool
    compliance_tags: List[str]

def validate_specs(state: AutomationState):
    required = ['protocol', 'ip_rating']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def check_compliance(state: AutomationState):
    tags = ['industrial_grade']
    if state.get('validation_passed'):
        tags.append('ready_for_procurement')
    return {'compliance_tags': tags}

graph = StateGraph(AutomationState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
process = graph.compile()
