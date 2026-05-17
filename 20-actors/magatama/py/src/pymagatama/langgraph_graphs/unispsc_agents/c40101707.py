from typing import TypedDict
from langgraph.graph import StateGraph, END

class CoolingTowerState(TypedDict):
    part_type: str
    spec_verified: bool
    compliance_score: int

def validate_part(state: CoolingTowerState):
    state['spec_verified'] = state['part_type'] in ['fill', 'nozzle', 'fan_blade']
    return state

def check_compliance(state: CoolingTowerState):
    state['compliance_score'] = 100 if state['spec_verified'] else 0
    return state

graph = StateGraph(CoolingTowerState)
graph.add_node('validate', validate_part)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()