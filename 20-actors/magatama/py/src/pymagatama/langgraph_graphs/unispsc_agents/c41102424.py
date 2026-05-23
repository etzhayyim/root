from typing import TypedDict
from langgraph.graph import StateGraph, END

class SlideWarmerState(TypedDict):
    temp_setting: float
    calibration_status: bool
    passed_validation: bool

def validate_specs(state: SlideWarmerState):
    valid = (30.0 <= state['temp_setting'] <= 75.0) and state['calibration_status']
    return {'passed_validation': valid}

graph = StateGraph(SlideWarmerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
