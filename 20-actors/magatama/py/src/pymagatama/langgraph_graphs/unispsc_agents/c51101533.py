from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class AlbuminState(TypedDict):
    batch_id: str
    purity: float
    temp_log: list[float]
    status: str

def validate_purity(state: AlbuminState) -> AlbuminState:
    if state['purity'] < 0.99:
        state['status'] = 'REJECTED_PURITY'
    else:
        state['status'] = 'PASSED_PURITY'
    return state

def check_cold_chain(state: AlbuminState) -> AlbuminState:
    if any(t > 8.0 for t in state['temp_log']):
        state['status'] = 'REJECTED_TEMPERATURE'
    elif state['status'] != 'REJECTED_PURITY':
        state['status'] = 'APPROVED'
    return state

graph = StateGraph(AlbuminState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_cold_chain', check_cold_chain)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_cold_chain')
graph.add_edge('check_cold_chain', END)
app = graph.compile()
