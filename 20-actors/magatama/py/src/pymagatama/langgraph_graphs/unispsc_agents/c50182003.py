from typing import TypedDict
from langgraph.graph import StateGraph, END

class DoughState(TypedDict):
    temp: float
    status: str

def validate_temp(state: DoughState):
    if state['temp'] <= -18.0:
        return {'status': 'PASSED'}
    return {'status': 'REJECTED'}

graph = StateGraph(DoughState)
graph.add_node('validate', validate_temp)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()