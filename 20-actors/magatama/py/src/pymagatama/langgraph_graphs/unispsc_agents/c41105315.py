from typing import TypedDict
from langgraph.graph import StateGraph, END

class GelDocState(TypedDict):
    part_number: str
    compatibility_verified: bool
    is_calibrated: bool

def check_compatibility(state: GelDocState):
    print(f'Checking compatibility for {state[\'part_number\']}')
    return {'compatibility_verified': True}

def verify_calibration(state: GelDocState):
    print('Verifying calibration requirements')
    return {'is_calibrated': True}

graph = StateGraph(GelDocState)
graph.add_node('check_comp', check_compatibility)
graph.add_node('verify_cal', verify_calibration)
graph.set_entry_point('check_comp')
graph.add_edge('check_comp', 'verify_cal')
graph.add_edge('verify_cal', END)
graph = graph.compile()