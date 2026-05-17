from typing import TypedDict
from langgraph.graph import StateGraph, END

class LightingControlState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_specs(state: LightingControlState):
    log = []
    required = ['Voltage Rating', 'Communication Protocol']
    for field in required:
        if field not in state['spec_data']:
            log.append(f'Missing: {field}')
    return {'validation_log': log, 'is_compliant': len(log) == 0}

def route_by_compliance(state: LightingControlState):
    return 'valid' if state['is_compliant'] else 'end'

graph = StateGraph(LightingControlState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()