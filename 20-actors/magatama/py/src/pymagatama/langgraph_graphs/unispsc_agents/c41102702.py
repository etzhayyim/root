from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScintillatorState(TypedDict):
    spec: dict
    validation_passed: bool
    compliance_risk: str

def validate_crystal_specs(state: ScintillatorState):
    required = ['resolution', 'decay_time', 'dimension']
    passed = all(k in state['spec'] for k in required)
    return {'validation_passed': passed}

def check_compliance(state: ScintillatorState):
    if state.get('dimension', 0) > 100: 
        return {'compliance_risk': 'high_export_control'} 
    return {'compliance_risk': 'low'}

graph = StateGraph(ScintillatorState)
graph.add_node('validate', validate_crystal_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')