from typing import TypedDict
from langgraph.graph import StateGraph, END

class CheeseState(TypedDict):
    origin: str
    temp_log: list
    is_compliant: bool

def validate_temp(state: CheeseState):
    state['is_compliant'] = all(t <= 5 for t in state['temp_log'])
    return state

def check_origin(state: CheeseState):
    print(f'Verifying import permits for: {state['origin']}')
    return state

graph = StateGraph(CheeseState)
graph.add_node('validate_temperature', validate_temp)
graph.add_node('check_origin', check_origin)
graph.add_edge('check_origin', 'validate_temperature')
graph.add_edge('validate_temperature', END)
graph.set_entry_point('check_origin')
