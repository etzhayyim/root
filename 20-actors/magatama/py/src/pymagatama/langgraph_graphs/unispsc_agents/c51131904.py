from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PlasmaState(TypedDict):
    batch_id: str
    temp_logs: List[float]
    safety_verified: bool

def validate_cold_chain(state: PlasmaState):
    avg_temp = sum(state['temp_logs']) / len(state['temp_logs'])
    return {'safety_verified': avg_temp <= -20.0}

def check_compliance(state: PlasmaState):
    print(f'Checking compliance for {state['batch_id']}')
    return {'safety_verified': True if state['safety_verified'] else False}

graph = StateGraph(PlasmaState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
