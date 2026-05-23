from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DefrostSystemState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: DefrostSystemState):
    required = ['voltage', 'thermal_capacity', 'airflow']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def generate_compliance(state: DefrostSystemState):
    if state['validation_passed']:
        return {'compliance_report': 'Certified for automotive defrost standard'}
    return {'compliance_report': 'Validation Failed: Missing specs'}

graph = StateGraph(DefrostSystemState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', generate_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
