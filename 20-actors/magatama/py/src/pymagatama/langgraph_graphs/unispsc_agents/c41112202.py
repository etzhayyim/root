from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeatTraceState(TypedDict):
    specs: dict
    validation_passed: bool
    risk_level: str

def validate_specs(state: HeatTraceState):
    required = ['voltage', 'wattage', 'certification']
    state['validation_passed'] = all(k in state['specs'] for k in required)
    return state

def evaluate_risk(state: HeatTraceState):
    state['risk_level'] = 'high' if state['specs'].get('temp_class') == 'T6' else 'standard'
    return state

graph = StateGraph(HeatTraceState)
graph.add_node('validate', validate_specs)
graph.add_node('risk', evaluate_risk)
graph.set_entry_point('validate')
graph.add_edge('validate', 'risk')
graph.add_edge('risk', END)
graph = graph.compile()
