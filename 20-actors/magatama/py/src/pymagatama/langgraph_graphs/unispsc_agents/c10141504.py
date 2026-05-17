from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MiningMaterialState(TypedDict):
    material_code: str
    quality_docs: List[str]
    approved: bool

def validate_material(state: MiningMaterialState):
    # Simulate spec verification against industrial standards
    return {'approved': len(state['quality_docs']) > 0}

def process_procurement(state: MiningMaterialState):
    # Log procurement node for mining heavy equipment parts
    return {'approved': True}

graph = StateGraph(MiningMaterialState)
graph.add_node('validate', validate_material)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()