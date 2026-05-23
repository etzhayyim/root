from typing import TypedDict
from langgraph.graph import StateGraph, END

class UrokinaseState(TypedDict):
    batch_id: str
    temp_log: float
    quality_cert: bool

def validate_cold_chain(state: UrokinaseState):
    if state['temp_log'] < 2.0 or state['temp_log'] > 8.0:
        return {'status': 'ALERT_TEMP_VIOLATION'}
    return {'status': 'VALID'}

def check_compliance(state: UrokinaseState):
    return {'compliant': state['quality_cert']}

graph = StateGraph(UrokinaseState)
graph.add_node('verify_temp', validate_cold_chain)
graph.add_node('compliance', check_compliance)
graph.add_edge('verify_temp', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('verify_temp')
compiled_graph = graph.compile()
