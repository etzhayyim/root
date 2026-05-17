from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CastingState(TypedDict):
    specs: dict
    validation_passed: bool
    inspection_report: str

def validate_specs(state: CastingState):
    required = ['material', 'tolerance', 'hardness']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def generate_report(state: CastingState):
    status = 'APPROVED' if state['validation_passed'] else 'REJECTED'
    return {'inspection_report': f'Casting QA Process: {status}'}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()