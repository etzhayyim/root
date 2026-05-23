from typing import TypedDict
from langgraph.graph import StateGraph, END

class VaccineState(TypedDict):
    lot_number: str
    temperature_logs: list
    is_compliant: bool

def validate_cold_chain(state: VaccineState):
    state['is_compliant'] = all(t >= 2 and t <= 8 for t in state['temperature_logs'])
    print(f'Cold chain status: {state['is_compliant']}')
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(VaccineState)
graph.add_node('validate', validate_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
