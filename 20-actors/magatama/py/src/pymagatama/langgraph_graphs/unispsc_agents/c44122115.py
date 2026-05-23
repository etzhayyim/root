from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    quantity: int
    material_type: str
    quality_check_passed: bool

def validate_materials(state: ProcurementState):
    # Validate if material is archival/acid-free for document preservation
    if state['material_type'] in ['acid-free', 'archival']:
        return {'quality_check_passed': True}
    return {'quality_check_passed': False}

def process_procurement(state: ProcurementState):
    return {'status': 'Approved' if state['quality_check_passed'] else 'Rejected'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_materials)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
