from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EnvelopeState(TypedDict):
    specifications: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: EnvelopeState):
    specs = state['specifications']
    passed = all(key in specs for key in ['material', 'dimensions', 'adhesive'])
    return {'validation_passed': passed, 'compliance_report': 'Passed' if passed else 'Missing data'}

def generate_procurement_order(state: EnvelopeState):
    return {'compliance_report': 'Order generated based on verified envelope specs'}

graph = StateGraph(EnvelopeState)
graph.add_node('validate', validate_specs)
graph.add_node('order', generate_procurement_order)
graph.add_edge('validate', 'order')
graph.add_edge('order', END)
graph.set_entry_point('validate')
