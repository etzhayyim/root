from typing import TypedDict
from langgraph.graph import StateGraph, END

class VaccineState(TypedDict):
    batch_id: str
    temperature_logs: list
    is_compliant: bool

def validate_cold_chain(state: VaccineState):
    state['is_compliant'] = all(temp < 8.0 for temp in state['temperature_logs'])
    print(f'Cold chain valid: {state['is_compliant']}')
    return 'end'

graph = StateGraph(VaccineState)
graph.add_node('validate', validate_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()