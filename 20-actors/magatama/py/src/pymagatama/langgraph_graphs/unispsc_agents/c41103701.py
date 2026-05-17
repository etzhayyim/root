from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabEquipmentState(TypedDict):
    temp_range: float
    flow_rate: float
    safety_certs: list
    validation_status: bool

def validate_specs(state: LabEquipmentState):
    if state['temp_range'] < 0:
        return {'validation_status': True}
    return {'validation_status': False}

def process_safety(state: LabEquipmentState):
    print(f'Checking safety compliance for {state['safety_certs']}')
    return state

graph = StateGraph(LabEquipmentState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', process_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()