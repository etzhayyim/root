from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MobileState(TypedDict):
    device_specs: dict
    compliance_passed: bool
    validation_log: List[str]

def validate_specs(state: MobileState):
    log = []
    passed = True
    if 'OS_version' not in state['device_specs']: 
        log.append('Missing OS version'); passed = False
    return {'compliance_passed': passed, 'validation_log': log}

def security_check(state: MobileState):
    return {'validation_log': state['validation_log'] + ['Security audit completed']}

graph = StateGraph(MobileState)
graph.add_node('validate', validate_specs)
graph.add_node('security', security_check)
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
graph.set_entry_point('validate')
graph = graph.compile()