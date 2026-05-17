from typing import TypedDict
from langgraph.graph import StateGraph, END

class PrimulaState(TypedDict):
    phytosanitary_cert: str
    temp_log: list
    validation_status: bool

def validate_phytosanitary(state: PrimulaState):
    return {'validation_status': state.get('phytosanitary_cert') is not None}

def check_cold_chain(state: PrimulaState):
    avg_temp = sum(state['temp_log']) / len(state['temp_log'])
    return {'validation_status': state['validation_status'] and (2 <= avg_temp <= 8)}

graph = StateGraph(PrimulaState)
graph.add_node('verify_docs', validate_phytosanitary)
graph.add_node('verify_logistics', check_cold_chain)
graph.set_entry_point('verify_docs')
graph.add_edge('verify_docs', 'verify_logistics')
graph.add_edge('verify_logistics', END)
graph = graph.compile()