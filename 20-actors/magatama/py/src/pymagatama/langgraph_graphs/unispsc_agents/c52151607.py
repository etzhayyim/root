from typing import TypedDict
from langgraph.graph import StateGraph, END

class MeasuringCupState(TypedDict):
    material: str
    capacity: float
    has_food_safety_cert: bool

def validate_material(state: MeasuringCupState):
    allowed = ['stainless steel', 'glass', 'pp', 'tritan']
    return {'is_valid': state['material'].lower() in allowed}

def check_certification(state: MeasuringCupState):
    return {'cert_valid': state['has_food_safety_cert']}

graph = StateGraph(MeasuringCupState)
graph.add_node('validate_spec', validate_material)
graph.add_node('check_cert', check_certification)
graph.set_entry_point('validate_spec')
graph.add_edge('validate_spec', 'check_cert')
graph.add_edge('check_cert', END)
graph = graph.compile()
