from typing import TypedDict
from langgraph.graph import StateGraph, END

class DairyState(TypedDict):
    temp: float
    is_compliant: bool

def check_temp(state: DairyState):
    state['is_compliant'] = -22.0 <= state['temp'] <= -18.0
    return state

workflow = StateGraph(DairyState)
workflow.add_node('check_temp', check_temp)
workflow.set_entry_point('check_temp')
workflow.add_edge('check_temp', END)
graph = workflow.compile()