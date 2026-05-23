from typing import TypedDict
from langgraph.graph import StateGraph, END

class CosyntropinState(TypedDict):
    batch_id: str
    purity_level: float
    temp_log: str
    validated: bool

def validate_purity(state: CosyntropinState):
    is_valid = state['purity_level'] >= 98.0
    return {'validated': is_valid}

def check_cold_chain(state: CosyntropinState):
    # Business logic for cold chain integrity
    return {'validated': state.get('validated', False) and 'correct' in state['temp_log']}

graph = StateGraph(CosyntropinState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_cold_chain', check_cold_chain)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_cold_chain')
graph.add_edge('check_cold_chain', END)
graph = graph.compile()
