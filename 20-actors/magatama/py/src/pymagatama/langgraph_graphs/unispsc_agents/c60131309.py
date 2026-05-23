from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class InstrumentState(TypedDict):
    instrument_id: str
    specs: dict
    validation_passed: bool
    inspection_report: str

def validate_specs(state: InstrumentState):
    required_keys = ['scale_length', 'tonewood', 'hardware_grade']
    passed = all(k in state['specs'] for k in required_keys)
    return {'validation_passed': passed}

def perform_inspection(state: InstrumentState):
    if state['validation_passed']:
        return {'inspection_report': 'Professional Grade Verified'}
    return {'inspection_report': 'Missing Documentation/Specs'}

graph = StateGraph(InstrumentState)
graph.add_node('validate', validate_specs)
graph.add_node('inspect', perform_inspection)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
app = graph.compile()
