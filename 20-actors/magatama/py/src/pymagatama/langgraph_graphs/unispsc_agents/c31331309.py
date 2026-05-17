from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    assembly_id: str
    material_spec: str
    weld_integrity_score: float
    compliance_checks: List[str]

def validate_weld_integrity(state: AssemblyState):
    if state['weld_integrity_score'] < 0.95:
        return {'compliance_checks': state['compliance_checks'] + ['Weld Strength Failed']}
    return {'compliance_checks': state['compliance_checks'] + ['Weld Strength Passed']}

def check_export_control(state: AssemblyState):
    return {'compliance_checks': state['compliance_checks'] + ['Export Control Screening Complete']}

graph = StateGraph(AssemblyState)
graph.add_node('validate_weld', validate_weld_integrity)
graph.add_node('check_export', check_export_control)
graph.set_entry_point('validate_weld')
graph.add_edge('validate_weld', 'check_export')
graph.add_edge('check_export', END)
graph = graph.compile()