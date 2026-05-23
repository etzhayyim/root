from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExamLightState(TypedDict):
    lux: int
    certified: bool
    compliant: bool

def validate_intensity(state: ExamLightState):
    state['compliant'] = state['lux'] >= 40000
    return state

def check_certification(state: ExamLightState):
    state['certified'] = True
    return state

graph = StateGraph(ExamLightState)
graph.add_node('validate_intensity', validate_intensity)
graph.add_node('check_certification', check_certification)
graph.set_entry_point('validate_intensity')
graph.add_edge('validate_intensity', 'check_certification')
graph.add_edge('check_certification', END)
graph = graph.compile()
