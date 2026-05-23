from typing import TypedDict
from langgraph.graph import StateGraph, END

class VaccineState(TypedDict):
    batch_id: str
    temp_log: list
    validation_status: bool

def validate_cold_chain(state: VaccineState):
    # Business logic for checking temperature logs against storage specs
    state['validation_status'] = all(t <= 8.0 and t >= 2.0 for t in state['temp_log'])
    print(f'Batch {state['batch_id']} valid: {state['validation_status']}')
    return 'validate_cold_chain'

graph = StateGraph(VaccineState)
graph.add_node('validate_cold_chain', validate_cold_chain)
graph.set_entry_point('validate_cold_chain')
graph.add_edge('validate_cold_chain', END)
graph = graph.compile()
