from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class LabPrintState(TypedDict):
    spec_requirements: dict
    validation_passed: bool
    compliance_flags: List[str]

def validate_specs(state: LabPrintState):
    # Business logic for validating lab printing equipment parameters
    required = ['resolution', 'chemical_compatibility']
    passed = all(k in state['spec_requirements'] for k in required)
    return {'validation_passed': passed}

def compliance_check(state: LabPrintState):
    # Dual-use assessment logic
    flags = []
    if state['spec_requirements'].get('resolution', 0) > 2400:
        flags.append('export-control-review')
    return {'compliance_flags': flags}

graph = StateGraph(LabPrintState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()