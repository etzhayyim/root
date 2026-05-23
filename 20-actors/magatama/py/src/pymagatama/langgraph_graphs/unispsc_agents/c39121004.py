from typing import TypedDict
from langgraph.graph import StateGraph, END

class PowerSupplyState(TypedDict):
    spec_data: dict
    compliance_verified: bool
    validation_log: list

def validate_specs(state: PowerSupplyState):
    log = []
    required = ['voltage', 'wattage', 'certification']
    for field in required:
        if field not in state['spec_data']:
            log.append(f'Missing {field}')
    return {'compliance_verified': len(log) == 0, 'validation_log': log}

def route_verification(state: PowerSupplyState):
    return 'valid' if state['compliance_verified'] else 'invalid'

graph = StateGraph(PowerSupplyState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
