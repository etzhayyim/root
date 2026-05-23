from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MarkerState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: List[str]

def validate_marker_spec(state: MarkerState):
    log = []
    compliant = True
    required_fields = ['material', 'standard', 'voltage_rating']
    for field in required_fields:
        if field not in state['spec_data']:
            log.append(f'Missing field: {field}')
            compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

graph = StateGraph(MarkerState)
graph.add_node('validate', validate_marker_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
