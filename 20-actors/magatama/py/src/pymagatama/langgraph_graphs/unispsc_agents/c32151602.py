from typing import TypedDict
from langgraph.graph import StateGraph, END

class PLCState(TypedDict):
    specs: dict
    validation_log: list
    is_compliant: bool

def validate_specs(state: PLCState):
    log = []
    required = ['bus_protocol_compatibility', 'IP_rating']
    valid = all(key in state['specs'] for key in required)
    log.append('Specs validated') if valid else log.append('Missing specs')
    return {'validation_log': log, 'is_compliant': valid}

def route_by_compliance(state: PLCState):
    return 'compliant_path' if state['is_compliant'] else 'reject_path'

graph = StateGraph(PLCState)
graph.add_node('validation', validate_specs)
graph.set_entry_point('validation')
graph.add_conditional_edges('validation', route_by_compliance, {'compliant_path': END, 'reject_path': END})
graph = graph.compile()
