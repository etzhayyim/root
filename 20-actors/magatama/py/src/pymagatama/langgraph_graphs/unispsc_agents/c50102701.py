from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FrozenFruitState(TypedDict):
    temp_log: List[float]
    safety_certs: List[str]
    approved: bool

def validate_temp(state: FrozenFruitState):
    avg = sum(state['temp_log']) / len(state['temp_log'])
    return {'approved': avg <= -18.0}

def check_certs(state: FrozenFruitState):
    return {'approved': len(state['safety_certs']) > 0}

graph = StateGraph(FrozenFruitState)
graph.add_node('temp_check', validate_temp)
graph.add_node('cert_check', check_certs)
graph.set_entry_point('temp_check')
graph.add_edge('temp_check', 'cert_check')
graph.add_edge('cert_check', END)
app = graph.compile()