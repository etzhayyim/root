from typing import TypedDict
from langgraph.graph import StateGraph, END

class AlteplaseState(TypedDict):
    batch_id: str
    temp_log: list
    is_compliant: bool

def validate_cold_chain(state: AlteplaseState):
    state['is_compliant'] = all(2 <= t <= 8 for t in state['temp_log'])
    print(f'Compliance check for batch {state['batch_id']}: {state['is_compliant']}')
    return 'end'

def check_expiry(state: AlteplaseState):
    return 'validate_cold_chain'

graph = StateGraph(AlteplaseState)
graph.add_node('check_expiry', check_expiry)
graph.add_node('validate_cold_chain', validate_cold_chain)
graph.set_entry_point('check_expiry')
graph.add_edge('check_expiry', 'validate_cold_chain')
graph.add_edge('validate_cold_chain', END)