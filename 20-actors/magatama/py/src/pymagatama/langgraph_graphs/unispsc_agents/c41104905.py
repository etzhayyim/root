from typing import TypedDict
from langgraph.graph import StateGraph, END

class FiltrationState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_risk: str

def validate_specs(state: FiltrationState):
    required = ['Material-Composition', 'Pore-Size-Microns']
    passed = all(k in state['specs'] for k in required)
    return {**state, 'validation_passed': passed}

def check_dual_use(state: FiltrationState):
    risk = 'HIGH' if state['specs'].get('Material-Composition') in ['Ceramic', 'Titanium'] else 'LOW'
    return {**state, 'compliance_risk': risk}

graph = StateGraph(FiltrationState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_dual_use)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()