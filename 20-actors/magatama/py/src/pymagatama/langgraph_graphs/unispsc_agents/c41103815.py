from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabEquipmentState(TypedDict):
    model_id: str
    speed_limits: tuple
    compliance_passed: bool

def validate_speed(state: LabEquipmentState):
    state['compliance_passed'] = 10 <= state['speed_limits'][1] <= 100
    return 'valid' if state['compliance_passed'] else 'failed'

def finalize_procurement(state: LabEquipmentState):
    return {'status': 'approved'}

graph = StateGraph(LabEquipmentState)
graph.add_node('validate', validate_speed)
graph.add_node('final', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph = graph.compile()
