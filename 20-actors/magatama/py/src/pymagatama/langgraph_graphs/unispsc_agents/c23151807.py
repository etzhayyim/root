from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LaserWeldState(TypedDict):
    specifications: dict
    compliance_check: bool
    safety_approval: bool

def validate_laser_specs(state: LaserWeldState):
    laser_class = state['specifications'].get('laser_safety_class', 0)
    return {'compliance_check': laser_class >= 4}

def perform_safety_risk_assessment(state: LaserWeldState):
    return {'safety_approval': state.get('compliance_check', False)}

graph = StateGraph(LaserWeldState)
graph.add_node('validate', validate_laser_specs)
graph.add_node('safety_check', perform_safety_risk_assessment)
graph.add_edge('validate', 'safety_check')
graph.add_edge('safety_check', END)
graph.set_entry_point('validate')
graph = graph.compile()