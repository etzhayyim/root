from typing import TypedDict
from langgraph.graph import StateGraph, END

class CircuitBreakerState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: CircuitBreakerState):
    log = []
    compliant = True
    required = ['Rated Current', 'Rated Voltage', 'Interrupting Capacity']
    for field in required:
        if field not in state['spec_data']:
            log.append(f'Missing {field}')
            compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

graph = StateGraph(CircuitBreakerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()