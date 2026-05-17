from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    part_specs: dict
    validation_status: bool
    compliance_report: str

def validate_dimension(state: ForgingState):
    specs = state['part_specs']
    is_valid = all(k in specs for k in ['tolerance', 'alloy_grade'])
    return {**state, 'validation_status': is_valid}

def generate_report(state: ForgingState):
    status = 'PASS' if state['validation_status'] else 'FAIL'
    return {**state, 'compliance_report': f'Inspection result: {status}'}

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_dimension)
graph.add_node('report', generate_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()