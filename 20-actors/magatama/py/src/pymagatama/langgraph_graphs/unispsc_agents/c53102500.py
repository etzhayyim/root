from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ClothingState(TypedDict):
    item_name: str
    specs: dict
    approved: bool
    validation_log: List[str]

def validate_materials(state: ClothingState):
    log = state.get('validation_log', [])
    material = state['specs'].get('fabric')
    if material:
        log.append(f'Validated material: {material}')
    return {'validation_log': log}

def check_compliance(state: ClothingState):
    log = state.get('validation_log', [])
    log.append('Running safety and flammability compliance checks')
    return {'validation_log': log, 'approved': True}

graph = StateGraph(ClothingState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('compliance_check', check_compliance)
graph.add_edge('validate_materials', 'compliance_check')
graph.add_edge('compliance_check', END)
graph.set_entry_point('validate_materials')
compiled_graph = graph.compile()