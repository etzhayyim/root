from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RawMaterialState(TypedDict):
    material_id: str
    purity: float
    compliance_docs: List[str]
    approved: bool

def validate_material(state: RawMaterialState):
    is_pure = state['purity'] >= 99.5
    has_docs = len(state['compliance_docs']) >= 2
    return {'approved': is_pure and has_docs}

def process_procurement(state: RawMaterialState):
    return {'status': 'processed' if state['approved'] else 'rejected'}

graph = StateGraph(RawMaterialState)
graph.add_node('validate', validate_material)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()