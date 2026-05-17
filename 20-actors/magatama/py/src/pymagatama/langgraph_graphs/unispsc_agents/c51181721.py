from typing import TypedDict
from langgraph.graph import StateGraph, END

class PeptideState(TypedDict):
    purity_certification: str
    temperature_logs: list
    validation_status: bool

def validate_cold_chain(state: PeptideState):
    # Logic to verify temperature integrity for sensitive peptides
    state['validation_status'] = all(t < -20 for t in state['temperature_logs'])
    print('Validation complete')
    return 'END'

graph = StateGraph(PeptideState)
graph.add_node('validate', validate_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()