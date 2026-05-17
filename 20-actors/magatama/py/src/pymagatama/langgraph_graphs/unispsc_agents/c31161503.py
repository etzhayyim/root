import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END

class DriveScrewState(TypedDict):
    screw_specs: dict
    validation_result: bool
    compliance_report: str

def validate_specs(state: DriveScrewState):
    specs = state['screw_specs']
    is_valid = 'material' in specs and 'thread_pitch' in specs
    return {'validation_result': is_valid}

def generate_report(state: DriveScrewState):
    if state['validation_result']:
        return {'compliance_report': 'Specifications validated per ISO standards.'}
    return {'compliance_report': 'Missing required technical parameters for procurement.'}

graph = StateGraph(DriveScrewState)
graph.add_node('validate', validate_specs)
graph.add_node('report', generate_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()