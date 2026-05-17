from typing import TypedDict
from langgraph.graph import StateGraph, END

class EggState(TypedDict):
    temp_celsius: float
    bacteria_count: int
    is_pasteurized: bool

def validate_safety(state: EggState):
    if not state.get('is_pasteurized'):
        return 'REJECT'
    if state.get('temp_celsius', 0) > 4:
        return 'REJECT'
    return 'APPROVE'

graph = StateGraph(EggState)
graph.add_node('safety_check', validate_safety)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()