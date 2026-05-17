from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MangoProcurementState(TypedDict):
    variety: str
    quality_score: float
    temp_records: List[float]
    approved: bool

def validate_cold_chain(state: MangoProcurementState) -> MangoProcurementState:
    avg_temp = sum(state['temp_records']) / len(state['temp_records'])
    state['approved'] = avg_temp < 12.0
    return state

def check_quality(state: MangoProcurementState) -> MangoProcurementState:
    if state['quality_score'] > 0.8:
        state['approved'] = True
    else:
        state['approved'] = False
    return state

graph = StateGraph(MangoProcurementState)
graph.add_node('validate_cold_chain', validate_cold_chain)
graph.add_node('check_quality', check_quality)
graph.set_entry_point('validate_cold_chain')
graph.add_edge('validate_cold_chain', 'check_quality')
graph.add_edge('check_quality', END)
app = graph.compile()