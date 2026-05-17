from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    batch_id: str
    temperature_log: list[float]
    is_compliant: bool

def validate_cold_chain(state: DrugState):
    state['is_compliant'] = all(2 <= t <= 8 for t in state['temperature_log'])
    return state

def check_regulatory(state: DrugState):
    if not state.get('batch_id'):
        state['is_compliant'] = False
    return state

graph = StateGraph(DrugState)
graph.add_node('validate_temp', validate_cold_chain)
graph.add_node('validate_reg', check_regulatory)
graph.set_entry_point('validate_temp')
graph.add_edge('validate_temp', 'validate_reg')
graph.add_edge('validate_reg', END)
graph = graph.compile()