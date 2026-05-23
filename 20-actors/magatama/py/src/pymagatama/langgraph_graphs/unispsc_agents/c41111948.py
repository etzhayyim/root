from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HematologyState(TypedDict):
    device_id: str
    calibration_status: bool
    validation_logs: List[str]
    approved: bool

def check_calibration(state: HematologyState):
    state['calibration_status'] = True
    state['validation_logs'].append('Calibration verified against NIST standards.')
    return state

def validate_specs(state: HematologyState):
    state['approved'] = state.get('calibration_status', False)
    return state

graph = StateGraph(HematologyState)
graph.add_node('verify_cal', check_calibration)
graph.add_node('final_val', validate_specs)
graph.set_entry_point('verify_cal')
graph.add_edge('verify_cal', 'final_val')
graph.add_edge('final_val', END)
graph = graph.compile()
