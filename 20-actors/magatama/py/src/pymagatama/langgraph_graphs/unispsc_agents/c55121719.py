from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SignalState(TypedDict):
    part_number: str
    spec_sheet: dict
    compliance_flag: bool
    validation_errors: List[str]

def validate_specs(state: SignalState):
    errors = []
    if state['spec_sheet'].get('voltage', 0) > 240:
        errors.append('Voltage exceeds high-risk threshold')
    return {'validation_errors': errors, 'compliance_flag': len(errors) == 0}

def check_export_control(state: SignalState):
    return {'compliance_flag': state['compliance_flag']}

graph = StateGraph(SignalState)
graph.add_node('validate', validate_specs)
graph.add_node('export', check_export_control)
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph.set_entry_point('validate')
graph = graph.compile()
