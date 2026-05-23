from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ConnectorState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_insulation(state: ConnectorState):
    voltage = state['spec_data'].get('voltage', 0)
    if voltage < 10: state['validation_errors'].append('Voltage rating too low for underground grade')
    return state

def check_ip_rating(state: ConnectorState):
    if state['spec_data'].get('ip_rating', 0) < 68: state['validation_errors'].append('Insufficient waterproof rating')
    return state

graph = StateGraph(ConnectorState)
graph.add_node('validate_insulation', validate_insulation)
graph.add_node('check_ip', check_ip_rating)
graph.set_entry_point('validate_insulation')
graph.add_edge('validate_insulation', 'check_ip')
graph.add_edge('check_ip', END)
graph = graph.compile()
