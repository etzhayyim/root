from typing import TypedDict
from langgraph.graph import StateGraph, END

class FreezerState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_freezing_specs(state: FreezerState):
    required = ['refrigerant', 'capacity', 'material']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed, 'compliance_report': 'Validated' if passed else 'Missing specs'}

def route_by_specs(state: FreezerState):
    return 'validate' if not state['validation_passed'] else END

graph = StateGraph(FreezerState)
graph.add_node('validate', validate_freezing_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
