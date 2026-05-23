from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    part_specs: dict
    validation_result: bool
    compliance_report: str

def validate_weld_integrity(state: AssemblyState):
    check = state['part_specs'].get('joint_tensile_strength_mpa', 0) > 400
    return {'validation_result': check}

def generate_report(state: AssemblyState):
    status = 'Pass' if state['validation_result'] else 'Fail'
    return {'compliance_report': f'Weld integrity assessment: {status}'}

graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_weld_integrity)
graph.add_node('report', generate_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph.compile()
