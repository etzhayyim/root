from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CellState(TypedDict):
    lot_number: str
    temp_log: List[float]
    is_viable: bool

def validate_cold_chain(state: CellState) -> CellState:
    # Logic to ensure the yeast competent cells stayed below -70C
    state['is_viable'] = all(temp <= -70 for temp in state['temp_log'])
    return state

def process_qc(state: CellState) -> CellState:
    # Logic to check transformation efficiency against specifications
    return state

graph = StateGraph(CellState)
graph.add_node('validate_cold_chain', validate_cold_chain)
graph.add_node('process_qc', process_qc)
graph.set_entry_point('validate_cold_chain')
graph.add_edge('validate_cold_chain', 'process_qc')
graph.add_edge('process_qc', END)
graph = graph.compile()