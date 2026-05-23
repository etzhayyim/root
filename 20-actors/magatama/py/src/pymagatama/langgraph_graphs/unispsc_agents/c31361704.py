from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    specification: dict
    validation_errors: List[str]
    approved: bool

def validate_material(state: ProcurementState):
    grade = state['specification'].get('material', '')
    if 'Inconel' not in grade:
        state['validation_errors'].append('Invalid material: Must be Inconel alloy')
    return state

def check_certification(state: ProcurementState):
    if not state['specification'].get('as9100_compliant', False):
        state['validation_errors'].append('Missing AS9100 certification')
    return state

def compile_procurement_graph():
    graph = StateGraph(ProcurementState)
    graph.add_node('validate_material', validate_material)
    graph.add_node('check_certification', check_certification)
    graph.set_entry_point('validate_material')
    graph.add_edge('validate_material', 'check_certification')
    graph.add_edge('check_certification', END)
    return graph.compile()

graph = compile_procurement_graph()
