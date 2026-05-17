from typing import TypedDict
from langgraph.graph import StateGraph, END

class SlipRingState(TypedDict):
    specs: dict
    validation_log: list
    compliant: bool

def validate_specs(state: SlipRingState):
    log = []
    required = ['voltage_rating', 'current_capacity', 'as9100_certified']
    for field in required:
        if field not in state['specs']:
            log.append(f'Missing {field}')
    return {'validation_log': log, 'compliant': len(log) == 0}

def route_by_compliance(state: SlipRingState):
    return 'process' if state['compliant'] else END

graph = StateGraph(SlipRingState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda x: {'validation_log': ['Proceeding to procurement logic']})
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()