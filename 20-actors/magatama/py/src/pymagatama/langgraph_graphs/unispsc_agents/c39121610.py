from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SurgeState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: SurgeState):
    log = []
    compliant = True
    required = ['voltage', 'surge_rating', 'standards']
    for field in required:
        if field not in state['specs']:
            compliant = False
            log.append(f'Missing field: {field}')
    return {'is_compliant': compliant, 'validation_log': log}

def route_by_compliance(state: SurgeState):
    return 'compliant_node' if state['is_compliant'] else 'reject_node'

graph = StateGraph(SurgeState)
graph.add_node('validate', validate_specs)
graph.add_node('compliant_node', lambda s: s)
graph.add_node('reject_node', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('compliant_node', END)
graph.add_edge('reject_node', END)
graph = graph.compile()
