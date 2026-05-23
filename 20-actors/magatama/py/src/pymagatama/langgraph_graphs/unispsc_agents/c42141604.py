from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BedpanState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: List[str]

def validate_materials(state: BedpanState):
    compliance = state['spec_data'].get('material') == 'medical-grade-polypropylene'
    return {'is_compliant': compliance, 'validation_log': ['Material checked']}

def check_dimensions(state: BedpanState):
    valid = state['spec_data'].get('height', 0) < 15
    return {'is_compliant': state['is_compliant'] and valid, 'validation_log': state['validation_log'] + ['Dimensions verified']}

graph = StateGraph(BedpanState)
graph.add_node('material_check', validate_materials)
graph.add_node('dim_check', check_dimensions)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'dim_check')
graph.add_edge('dim_check', END)
graph = graph.compile()
