from typing import TypedDict
from langgraph.graph import StateGraph, END

class GolfState(TypedDict):
    equipment_data: dict
    validation_passed: bool

def validate_certification(state: GolfState):
    print('Validating equipment against USGA/R&A standards...')
    state['validation_passed'] = 'certification' in state['equipment_data']
    return state

def check_quality(state: GolfState):
    print('Checking material quality and durability specs...')
    return state

graph = StateGraph(GolfState)
graph.add_node('cert_check', validate_certification)
graph.add_node('quality_check', check_quality)
graph.set_entry_point('cert_check')
graph.add_edge('cert_check', 'quality_check')
graph.add_edge('quality_check', END)
graph = graph.compile()