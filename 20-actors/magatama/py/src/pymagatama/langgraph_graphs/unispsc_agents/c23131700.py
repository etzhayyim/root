from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LaserProcState(TypedDict):
    laser_spec: dict
    compliance_check: bool
    safety_approval: bool

def validate_specs(state: LaserProcState):
    power = state['laser_spec'].get('power', 0)
    return {'compliance_check': power > 0 and power < 6}

def check_safety(state: LaserProcState):
    return {'safety_approval': True}

graph = StateGraph(LaserProcState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', check_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()