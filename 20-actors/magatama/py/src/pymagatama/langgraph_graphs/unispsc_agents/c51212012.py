from typing import TypedDict
from langgraph.graph import StateGraph, END

class CorianderState(TypedDict):
    quality_score: float
    temp_log: list
    passed_inspection: bool

def validate_freshness(state: CorianderState):
    state['passed_inspection'] = all(t < 5.0 for t in state['temp_log'])
    print(f'Inspection result: {state['passed_inspection']}')
    return state

graph = StateGraph(CorianderState)
graph.add_node('inspection', validate_freshness)
graph.set_entry_point('inspection')
graph.add_edge('inspection', END)
graph = graph.compile()
