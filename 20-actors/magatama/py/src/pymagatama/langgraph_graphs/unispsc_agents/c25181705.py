from typing import TypedDict
from langgraph.graph import StateGraph, END

class TrailerState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_thermal(state: TrailerState):
    temp_range = state['spec_data'].get('temp_range', 0)
    state['validation_passed'] = temp_range < -18
    return state

def check_compliance(state: TrailerState):
    state['compliance_report'] = 'Certified for food safety' if state['validation_passed'] else 'Manual review required'
    return state

graph = StateGraph(TrailerState)
graph.add_node('thermal_check', validate_thermal)
graph.add_node('compliance_log', check_compliance)
graph.set_entry_point('thermal_check')
graph.add_edge('thermal_check', 'compliance_log')
graph.add_edge('compliance_log', END)
app = graph.compile()
