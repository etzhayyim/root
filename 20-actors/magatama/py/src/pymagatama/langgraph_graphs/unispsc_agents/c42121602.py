from typing import TypedDict
from langgraph.graph import StateGraph, END

class BloodProductState(TypedDict):
    batch_id: str
    temp_log: float
    gmp_verified: bool
    status: str

def validate_gmp(state: BloodProductState):
    state['gmp_verified'] = True
    return {'status': 'CERTIFIED' if state['gmp_verified'] else 'REJECTED'}

def check_temp(state: BloodProductState):
    return {'status': 'VALID' if 2.0 <= state['temp_log'] <= 8.0 else 'EXPIRED'}

graph = StateGraph(BloodProductState)
graph.add_node('verify', validate_gmp)
graph.add_node('check', check_temp)
graph.set_entry_point('verify')
graph.add_edge('verify', 'check')
graph.add_edge('check', END)
graph = graph.compile()