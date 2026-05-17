from typing import TypedDict
from langgraph.graph import StateGraph, END

class TrafficState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: TrafficState) -> TrafficState:
    # Specialized logic for traffic control compliance
    required = ['voltage', 'ip_rating', 'iso_compliance']
    missing = [req for req in required if req not in state['spec_data']]
    return {'validated': len(missing) == 0, 'error_log': missing}

def route_by_validation(state: TrafficState) -> str:
    return 'process' if state['validated'] else 'reject'

graph = StateGraph(TrafficState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()