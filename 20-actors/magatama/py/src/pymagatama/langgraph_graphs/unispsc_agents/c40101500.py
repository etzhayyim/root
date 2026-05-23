from typing import TypedDict
from langgraph.graph import StateGraph, END

class VentilationState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: VentilationState):
    required_keys = ['airflow', 'power', 'noise']
    passed = all(key in state['specs'] for key in required_keys)
    return {'validation_passed': passed, 'compliance_report': 'Validated' if passed else 'Error'}

def finalize_order(state: VentilationState):
    return {'compliance_report': 'Procurement order ready for authorization'}

graph = StateGraph(VentilationState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
