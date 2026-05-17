from typing import TypedDict
from langgraph.graph import StateGraph, END

class DSLProcurementState(TypedDict):
    spec_requirements: dict
    validation_report: list
    compliance_ok: bool

def validate_specs(state: DSLProcurementState):
    report = []
    if 'port_configuration' not in state['spec_requirements']:
        report.append('Missing port density requirements')
    return {'validation_report': report, 'compliance_ok': len(report) == 0}

def route_by_compliance(state: DSLProcurementState):
    return 'process_order' if state['compliance_ok'] else 'request_revision'

graph = StateGraph(DSLProcurementState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', 'process_order')
graph.set_entry_point('validate')
graph.set_finish_point('process_order')
compiled_graph = graph.compile()