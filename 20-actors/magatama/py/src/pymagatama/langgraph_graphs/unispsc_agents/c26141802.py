from typing import TypedDict
from langgraph.graph import StateGraph, END

class HotCellDeviceState(TypedDict):
    device_id: str
    radiation_rating: float
    inspection_passed: bool

def validate_radiation_spec(state: HotCellDeviceState):
    state['inspection_passed'] = state['radiation_rating'] > 10000
    return state

def execute_risk_assessment(state: HotCellDeviceState):
    print(f'Assessing dual-use risks for device: {state["device_id"]}')
    return state

graph = StateGraph(HotCellDeviceState)
graph.add_node('validate', validate_radiation_spec)
graph.add_node('risk_check', execute_risk_assessment)
graph.set_entry_point('validate')
graph.add_edge('validate', 'risk_check')
graph.add_edge('risk_check', END)
graph = graph.compile()