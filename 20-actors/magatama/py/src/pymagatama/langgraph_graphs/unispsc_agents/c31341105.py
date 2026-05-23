from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    material_spec: dict
    validation_passed: bool
    compliance_flags: list

def validate_materials(state: AssemblyState):
    compliant = state['material_spec'].get('grade') in ['4130', '4140']
    return {'validation_passed': compliant}

def check_welding_compliance(state: AssemblyState):
    flags = ['ISO3834_Check'] if state['validation_passed'] else ['FAIL_REJECTED']
    return {'compliance_flags': flags}

graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_materials)
graph.add_node('weld_check', check_welding_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'weld_check')
graph.add_edge('weld_check', END)
graph = graph.compile()
