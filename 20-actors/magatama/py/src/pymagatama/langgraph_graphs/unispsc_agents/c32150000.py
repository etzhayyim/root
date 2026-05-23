from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AutomationState(TypedDict):
    specs: dict
    validation_passed: bool
    error_logs: List[str]

def validate_specs(state: AutomationState):
    required = ['Voltage', 'Protocol', 'IP_Rating']
    passed = all(k in state['specs'] for k in required)
    state['validation_passed'] = passed
    if not passed: state['error_logs'].append('Missing mandatory spec fields')
    return {'validation_passed': passed}

def route_verification(state: AutomationState):
    return 'valid' if state['validation_passed'] else 'invalid'

graph = StateGraph(AutomationState)
graph.add_node('validator', validate_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph.compile()
