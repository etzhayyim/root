from typing import TypedDict
from langgraph.graph import StateGraph, END

class GlucagonState(TypedDict):
    batch_id: str
    temp_log: list[float]
    is_compliant: bool

def validate_cold_chain(state: GlucagonState):
    state['is_compliant'] = all(2.0 <= t <= 8.0 for t in state['temp_log'])
    print(f'Batch {state['batch_id']} compliance: {state['is_compliant']}')
    return 'end'

def create_graph():
    graph = StateGraph(GlucagonState)
    graph.add_node('cold_chain', validate_cold_chain)
    graph.set_entry_point('cold_chain')
    graph.add_edge('cold_chain', END)
    return graph.compile()

graph = create_graph()
