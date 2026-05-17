from typing import TypedDict
from langgraph.graph import StateGraph, END

class DiodeState(TypedDict):
    part_number: str
    specs: dict
    is_compliant: bool

def validate_specs(state: DiodeState):
    # Business logic for diode specification compliance
    required = ['peak_inverse_voltage', 'forward_current_rating']
    state['is_compliant'] = all(k in state['specs'] for k in required)
    return state

def finalize_order(state: DiodeState):
    return {'status': 'processed' if state['is_compliant'] else 'rejected'}

graph = StateGraph(DiodeState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()