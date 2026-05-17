from typing import TypedDict
from langgraph.graph import StateGraph, END

class VacuumSystemState(TypedDict):
    pressure: float
    temp: float
    status: str

def validate_pressure(state: VacuumSystemState):
    return {'status': 'VALID' if state['pressure'] < 1e-4 else 'INVALID'}

def check_temp(state: VacuumSystemState):
    return {'status': 'CRITICAL' if state['temp'] > 1200 else 'READY'}

graph = StateGraph(VacuumSystemState)
graph.add_node('validate_pressure', validate_pressure)
graph.add_node('check_temp', check_temp)
graph.set_entry_point('validate_pressure')
graph.add_edge('validate_pressure', 'check_temp')
graph.add_edge('check_temp', END)
app = graph.compile()