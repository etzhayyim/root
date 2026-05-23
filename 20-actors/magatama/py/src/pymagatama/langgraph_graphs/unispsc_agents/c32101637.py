from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessorState(TypedDict):
    spec_data: dict
    validation_report: dict
    is_compliant: bool

def validate_tech_specs(state: ProcessorState):
    specs = state['spec_data']
    checks = {'throughput_check': specs.get('throughput', 0) > 0, 'export_control': True}
    return {'validation_report': checks, 'is_compliant': all(checks.values())}

def check_compliance(state: ProcessorState):
    return 'compliant' if state['is_compliant'] else 'flag_for_review'

graph = StateGraph(ProcessorState)
graph.add_node('validate', validate_tech_specs)
graph.add_conditional_edges('validate', check_compliance, {'compliant': END, 'flag_for_review': END})
graph.set_entry_point('validate')
