from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CytologyState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_stability(state: CytologyState):
    temp = state['spec_data'].get('storage_temp')
    if not (-20 <= temp <= 8):
        state['validation_errors'].append('Temperature deviation detected')
    return state

def check_certification(state: CytologyState):
    if 'ISO_13485' not in state['spec_data'].get('certs', []):
        state['is_compliant'] = False
    return state

graph = StateGraph(CytologyState)
graph.add_node('validate_stability', validate_stability)
graph.add_node('check_certification', check_certification)
graph.set_entry_point('validate_stability')
graph.add_edge('validate_stability', 'check_certification')
graph.add_edge('check_certification', END)
app = graph.compile()