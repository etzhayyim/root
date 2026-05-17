from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StructuralState(TypedDict):
    material_grade: str
    torque_specs: float
    validation_status: bool
    compliance_report: str

def validate_materials(state: StructuralState):
    if state['material_grade'] in ['SUS304', 'SUS316']:
        state['validation_status'] = True
        state['compliance_report'] = 'Material verified.'
    else:
        state['validation_status'] = False
        state['compliance_report'] = 'Invalid material grade.'
    return state

def check_torque(state: StructuralState):
    if state['torque_specs'] > 0:
        state['compliance_report'] += ' Torque specs confirmed.'
    return state

graph = StateGraph(StructuralState)
graph.add_node('validate', validate_materials)
graph.add_node('torque', check_torque)
graph.add_edge('validate', 'torque')
graph.add_edge('torque', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()