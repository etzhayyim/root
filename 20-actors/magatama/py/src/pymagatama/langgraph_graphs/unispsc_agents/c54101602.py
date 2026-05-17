from typing import TypedDict
from langgraph.graph import StateGraph, END

class NecklaceState(TypedDict):
    material: str
    value: float
    certs: list
    validation_status: str

def validate_materials(state: NecklaceState):
    # Business logic for precious metal verification
    if state['material'] in ['Gold', 'Platinum', 'Silver']:
        return {'validation_status': 'Verified_Material'}
    return {'validation_status': 'Material_Review_Manual'}

def check_certs(state: NecklaceState):
    if len(state['certs']) >= 2:
        return {'validation_status': 'Ready_For_Acquisition'}
    return {'validation_status': 'Missing_Certs_Flag'}

graph = StateGraph(NecklaceState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_certs', check_certs)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'check_certs')
graph.add_edge('check_certs', END)
app = graph.compile()