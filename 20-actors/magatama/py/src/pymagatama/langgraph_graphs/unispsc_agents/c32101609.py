from typing import TypedDict
from langgraph.graph import StateGraph, END

class ASICState(TypedDict):
    spec_sheet: dict
    validation_passed: bool
    export_control_check: bool

def validate_asic_specs(state: ASICState):
    specs = state['spec_sheet']
    passed = 'nm' in specs and 'gate_count' in specs
    return {'validation_passed': passed}

def check_export(state: ASICState):
    return {'export_control_check': True}

graph = StateGraph(ASICState)
graph.add_node('validate', validate_asic_specs)
graph.add_node('export_review', check_export)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
graph = graph.compile()
