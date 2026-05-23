from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    batch_id: str
    purity_level: float
    temp_log: float
    is_compliant: bool

def validate_purity(state: PharmState) -> PharmState:
    state['is_compliant'] = state['purity_level'] >= 99.5
    return state

def check_temp(state: PharmState) -> PharmState:
    if state['temp_log'] > 8.0: state['is_compliant'] = False
    return state

graph = StateGraph(PharmState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_temp', check_temp)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_temp')
graph.add_edge('check_temp', END)
compiled_graph = graph.compile()
