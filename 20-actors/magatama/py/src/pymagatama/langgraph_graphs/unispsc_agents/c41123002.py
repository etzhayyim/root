from typing import TypedDict
from langgraph.graph import StateGraph, END

class DesiccatorState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: DesiccatorState):
    required = ['humidity_range', 'sealing_type']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed, 'compliance_report': 'Validated' if passed else 'Missing Specs'}

def finalize_order(state: DesiccatorState):
    return {'compliance_report': 'Order ready for procurement'}

graph = StateGraph(DesiccatorState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()