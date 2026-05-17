from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftSystemState(TypedDict):
    part_id: str
    safety_clearance: bool
    compliance_docs: list[str]

def validate_certification(state: AircraftSystemState):
    state['safety_clearance'] = 'AS9100' in state['compliance_docs']
    return state

def check_compliance(state: AircraftSystemState):
    return 'compliant' if state['safety_clearance'] else 'non_compliant'

graph = StateGraph(AircraftSystemState)
graph.add_node('validate', validate_certification)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_compliance, {'compliant': END, 'non_compliant': END})
graph.compile()