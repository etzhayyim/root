from typing import TypedDict
from langgraph.graph import StateGraph, END

class AmifostineState(TypedDict):
    batch_id: str
    temp_log: list
    is_compliant: bool

def validate_cold_chain(state: AmifostineState):
    temp_threshold = 8.0
    state['is_compliant'] = all(t <= temp_threshold for t in state['temp_log'])
    return state

def check_quality(state: AmifostineState):
    # Simulate GMP certification check
    return {'is_compliant': state['is_compliant'] and True}

graph = StateGraph(AmifostineState)
graph.add_node('validate_chain', validate_cold_chain)
graph.add_node('check_quality', check_quality)
graph.add_edge('validate_chain', 'check_quality')
graph.add_edge('check_quality', END)
graph.set_entry_point('validate_chain')
graph = graph.compile()
