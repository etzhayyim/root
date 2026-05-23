from typing import TypedDict
from langgraph.graph import StateGraph, END

class RoadProjectState(TypedDict):
    spec_compliance: bool
    safety_check_passed: bool

def validate_materials(state: RoadProjectState):
    state['spec_compliance'] = True
    return 'check_safety'

def verify_safety(state: RoadProjectState):
    state['safety_check_passed'] = True
    return END

graph = StateGraph(RoadProjectState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_safety', verify_safety)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'check_safety')
graph.add_edge('check_safety', END)
graph = graph.compile()
