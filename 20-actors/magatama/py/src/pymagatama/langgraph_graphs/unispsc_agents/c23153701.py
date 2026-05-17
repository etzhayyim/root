from typing import TypedDict
from langgraph.graph import StateGraph, END

class LaserProcState(TypedDict):
    specs: dict
    validation_results: dict
    approved: bool

def validate_safety(state: LaserProcState):
    laser_class = state['specs'].get('laser_class')
    is_safe = laser_class in ['Class 1', 'Class 2']
    return {'validation_results': {'safety_check': is_safe}}

def check_compliance(state: LaserProcState):
    compliance = state['specs'].get('certifications', [])
    approved = 'CE' in compliance and 'FDA' in compliance
    return {'approved': approved}

graph = StateGraph(LaserProcState)
graph.add_node('safety', validate_safety)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('safety')
graph.add_edge('safety', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()