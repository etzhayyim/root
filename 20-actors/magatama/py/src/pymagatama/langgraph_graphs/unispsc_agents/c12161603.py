from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MaterialProcurementState(TypedDict):
    material_id: str
    purity: float
    specs: dict
    approved: bool
    validation_log: List[str]

def validate_material_purity(state: MaterialProcurementState):
    if state['purity'] >= 99.99:
        return {'approved': True, 'validation_log': ['Purity validated > 99.99%']}
    return {'approved': False, 'validation_log': ['Purity insufficient for high-spec manufacturing']}

def check_certification(state: MaterialProcurementState):
    if 'certification_iso9001' in state['specs']:
        return {'validation_log': state['validation_log'] + ['ISO9001 certification found']}
    return {'approved': False, 'validation_log': state['validation_log'] + ['Missing ISO9001 certification']}

graph = StateGraph(MaterialProcurementState)
graph.add_node('validate_purity', validate_material_purity)
graph.add_node('check_cert', check_certification)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_cert')
graph.add_edge('check_cert', END)
graph = graph.compile()