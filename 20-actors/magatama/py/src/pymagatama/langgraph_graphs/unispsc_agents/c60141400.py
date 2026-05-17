from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PlayEquipmentState(TypedDict):
    item_name: str
    safety_certifications: List[str]
    is_compliant: bool

def validate_safety(state: PlayEquipmentState):
    required = {'ASTM', 'EN71'}
    compliant = all(cert in state['safety_certifications'] for cert in required)
    return {'is_compliant': compliant}

def route_by_compliance(state: PlayEquipmentState):
    return 'approved' if state['is_compliant'] else 'rejected'

graph = StateGraph(PlayEquipmentState)
graph.add_node('safety_check', validate_safety)
graph.add_edge('safety_check', END)
graph.set_entry_point('safety_check')
graph = graph.compile()