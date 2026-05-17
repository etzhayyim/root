from typing import TypedDict
from langgraph.graph import StateGraph, END

class CompressorState(TypedDict):
    spec_data: dict
    validation_passed: bool
    safety_check: str

def validate_specs(state: CompressorState):
    specs = state['spec_data']
    passed = all(k in specs for k in ['psi', 'cfm']) and specs['psi'] > 0
    return {'validation_passed': passed}

def safety_compliance(state: CompressorState):
    return {'safety_check': 'COMPLIANT' if state['validation_passed'] else 'REJECTED'}

graph = StateGraph(CompressorState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_compliance)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
app = graph.compile()