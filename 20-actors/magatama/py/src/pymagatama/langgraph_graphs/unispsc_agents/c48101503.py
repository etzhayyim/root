from typing import TypedDict
from langgraph.graph import StateGraph, END

class BroilerState(TypedDict):
    batch_id: str
    health_certs: bool
    temp_log: float
    status: str

def validate_certs(state: BroilerState):
    state['status'] = 'CERTIFIED' if state['health_certs'] else 'REJECTED'
    return state

def check_cold_chain(state: BroilerState):
    if state['temp_log'] > 4.0:
        state['status'] = 'spoiled'
    return state

graph = StateGraph(BroilerState)
graph.add_node('validate', validate_certs)
graph.add_node('check_temp', check_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_temp')
graph.add_edge('check_temp', END)

graph = graph.compile()