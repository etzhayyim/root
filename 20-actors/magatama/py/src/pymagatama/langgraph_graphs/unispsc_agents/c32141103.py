from typing import TypedDict
from langgraph.graph import StateGraph, END

class GridDeviceState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: GridDeviceState):
    specs = state['spec_data']
    passed = 'iec_61850_compliance' in specs and specs['voltage_rating_kv'] > 0
    return {'validation_passed': passed, 'compliance_report': 'Validated' if passed else 'Failed'}

workflow = StateGraph(GridDeviceState)
workflow.add_node('validation', validate_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
