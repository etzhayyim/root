from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ActuatorState(TypedDict):
    specs: dict
    validation_logs: List[str]
    approved: bool

def validate_pressure_rating(state: ActuatorState):
    pressure = state['specs'].get('pressure', 0)
    if pressure > 1000:
        state['validation_logs'].append('High pressure alert: Requires secondary inspection')
    return {'validation_logs': state['validation_logs']}

def check_compliance(state: ActuatorState):
    state['approved'] = 'ISO_Cert' in state['specs']
    return {'approved': state['approved']}

graph = StateGraph(ActuatorState)
graph.add_node('validate_pressure', validate_pressure_rating)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('validate_pressure')
graph.add_edge('validate_pressure', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()
