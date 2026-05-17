from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ServoState(TypedDict):
    servo_id: str
    torque_spec: float
    test_results: List[dict]
    status: str

def validate_torque(state: ServoState):
    # Simulate CAD/Spec validation for 20122005 class
    if state['torque_spec'] < 5.0:
        return {'status': 'rejected_insufficient_torque'}
    return {'status': 'torque_validated'}

def perform_inspection(state: ServoState):
    # Simulate robotic hardware inspection workflow
    return {'test_results': [{'test': 'thermal_stress', 'passed': True}]}

graph = StateGraph(ServoState)
graph.add_node('validate_torque', validate_torque)
graph.add_node('perform_inspection', perform_inspection)
graph.set_entry_point('validate_torque')
graph.add_edge('validate_torque', 'perform_inspection')
graph.add_edge('perform_inspection', END)
graph = graph.compile()