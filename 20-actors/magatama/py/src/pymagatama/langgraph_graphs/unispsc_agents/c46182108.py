from typing import TypedDict
from langgraph.graph import StateGraph, END

class AntistaticSpecState(TypedDict):
    resistance: float
    compliance_cert: str
    is_valid: bool

def validate_resistance(state: AntistaticSpecState):
    # Industry standard for ESD straps is typically 10^5 to 10^9 ohms
    state['is_valid'] = 1e5 <= state['resistance'] <= 1e9
    return state

def check_compliance(state: AntistaticSpecState):
    state['is_valid'] = bool(state['compliance_cert'] == 'ESD S20.20')
    return state

graph = StateGraph(AntistaticSpecState)
graph.add_node('val_res', validate_resistance)
graph.add_node('val_cert', check_compliance)
graph.set_entry_point('val_res')
graph.add_edge('val_res', 'val_cert')
graph.add_edge('val_cert', END)
graph = graph.compile()