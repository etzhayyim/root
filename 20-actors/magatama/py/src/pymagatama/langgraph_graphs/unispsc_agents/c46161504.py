from typing import TypedDict
from langgraph.graph import StateGraph, END

class TrafficSignalState(TypedDict):
    spec_data: dict
    validation_log: list

def validate_specs(state: TrafficSignalState):
    log = []
    if 'IP_rating' not in state['spec_data']:
        log.append('Missing IP rating')
    return {'validation_log': log}

def approve_procurement(state: TrafficSignalState):
    return {'validation_log': state['validation_log'] + ['Procurement approved']}

graph = StateGraph(TrafficSignalState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approve_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
