from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict

class PharmState(TypedDict):
    batch_id: str
    purity_level: float
    temp_log: float
    compliant: bool

def validate_specs(state: PharmState) -> PharmState:
    state['compliant'] = state['purity_level'] >= 99.0 and state['temp_log'] < 25.0
    return state

def route_by_compliance(state: PharmState) -> str:
    return 'process' if state['compliant'] else 'reject'

graph = StateGraph(PharmState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', 'process')
graph.set_entry_point('validate')
graph.add_edge('process', END)
graph = graph.compile()