from typing import TypedDict
from langgraph.graph import StateGraph, END

class HIDState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_ballast_specs(state: HIDState):
    log = []
    required = ['voltage', 'wattage', 'certification']
    for field in required:
        if field not in state['spec_data']:
            log.append(f'Missing required spec: {field}')
    return {'validation_log': log, 'is_compliant': len(log) == 0}

def check_compliance(state: HIDState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(HIDState)
graph.add_node('validation', validate_ballast_specs)
graph.set_entry_point('validation')
graph.add_conditional_edges('validation', check_compliance, {'compliant': END, 'non_compliant': END})
graph.compile()