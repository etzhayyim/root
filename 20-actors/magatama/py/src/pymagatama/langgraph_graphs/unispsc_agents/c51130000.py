from typing import TypedDict, List
from langgraph.graph import StateGraph

class HematologyState(TypedDict):
    batch_id: str
    compliance_status: bool
    temp_log: List[float]

def validate_cold_chain(state: HematologyState):
    avg_temp = sum(state['temp_log']) / len(state['temp_log'])
    return {'compliance_status': 2 <= avg_temp <= 8}

def update_compliance(state: HematologyState):
    return {'compliance_status': True}

graph = StateGraph(HematologyState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('finalize', update_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.set_finish_point('finalize')
graph = graph.compile()
