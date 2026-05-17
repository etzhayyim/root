from langgraph.graph import StateGraph, END
from typing import TypedDict
class FrozenFruitState(TypedDict):
    temperature: float
    haccp_compliant: bool
    is_approved: bool
def check_temp(state: FrozenFruitState):
    return {'is_approved': state['temperature'] <= -18.0 and state['haccp_compliant']}
graph = StateGraph(FrozenFruitState)
graph.add_node('validation', check_temp)
graph.add_edge('validation', END)
graph.set_entry_point('validation')
graph = graph.compile()