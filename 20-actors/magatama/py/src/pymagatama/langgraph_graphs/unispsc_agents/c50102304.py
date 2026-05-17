from typing import TypedDict
from langgraph.graph import StateGraph, END

class PapayaState(TypedDict):
    ripeness: float
    temp: float
    is_compliant: bool

def check_ripeness(state: PapayaState):
    return {'is_compliant': 0.3 <= state['ripeness'] <= 0.8}

def check_temp(state: PapayaState):
    return {'is_compliant': state['temp'] <= 12.0}

graph = StateGraph(PapayaState)
graph.add_node('ripeness_check', check_ripeness)
graph.add_node('temp_check', check_temp)
graph.set_entry_point('ripeness_check')
graph.add_edge('ripeness_check', 'temp_check')
graph.add_edge('temp_check', END)
app = graph.compile()