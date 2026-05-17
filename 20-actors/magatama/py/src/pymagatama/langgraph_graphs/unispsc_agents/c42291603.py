from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SurgicalToolState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: List[str]

def validate_materials(state: SurgicalToolState):
    material = state['spec_data'].get('material', '')
    is_compliant = 'Stainless Steel' in material
    return {'is_compliant': is_compliant, 'validation_log': ['Material verified']}

def check_certifications(state: SurgicalToolState):
    has_iso = state['spec_data'].get('iso_13485', False)
    return {'is_compliant': state['is_compliant'] and has_iso, 'validation_log': state['validation_log'] + ['ISO checked']}

graph = StateGraph(SurgicalToolState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_certifications', check_certifications)
graph.add_edge('validate_materials', 'check_certifications')
graph.add_edge('check_certifications', END)
graph.set_entry_point('validate_materials')
graph = graph.compile()