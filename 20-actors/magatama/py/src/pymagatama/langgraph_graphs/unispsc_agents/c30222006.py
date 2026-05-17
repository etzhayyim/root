from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RailStationState(TypedDict):
    requirements: List[str]
    validation_checks: List[str]
    approved: bool

def validate_safety_standards(state: RailStationState):
    state['validation_checks'].append('Safety Standards Verified')
    return {'validation_checks': state['validation_checks']}

def check_infrastructure_integrity(state: RailStationState):
    state['validation_checks'].append('Infrastructure Integrity Confirmed')
    return {'validation_checks': state['validation_checks'], 'approved': True}

graph = StateGraph(RailStationState)
graph.add_node('safety_check', validate_safety_standards)
graph.add_node('infra_check', check_infrastructure_integrity)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'infra_check')
graph.add_edge('infra_check', END)
graph = graph.compile()