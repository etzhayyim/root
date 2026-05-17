from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FollitropinState(TypedDict):
    batch_id: str
    temperature_logs: List[float]
    is_compliant: bool

def validate_cold_chain(state: FollitropinState):
    avg_temp = sum(state['temperature_logs']) / len(state['temperature_logs'])
    return {'is_compliant': 2.0 <= avg_temp <= 8.0}

def approval_node(state: FollitropinState):
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(FollitropinState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('approval', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()