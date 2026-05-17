from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AuditState(TypedDict):
    material_spec: str
    ndt_results: bool
    is_compliant: bool

def validate_material(state: AuditState):
    return {'is_compliant': state['material_spec'] == 'WASPALLOY_AMSR_STD' and state['ndt_results']}

def process_assembly(state: AuditState):
    return {'is_compliant': True}

graph = StateGraph(AuditState)
graph.add_node('validate', validate_material)
graph.add_node('process', process_assembly)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()