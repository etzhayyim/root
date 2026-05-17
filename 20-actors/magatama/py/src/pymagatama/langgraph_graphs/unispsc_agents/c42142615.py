from typing import TypedDict
from langgraph.graph import StateGraph, END

class SyringeState(TypedDict):
    spec_data: dict
    validation_status: bool

def validate_certification(state: SyringeState):
    cert = state['spec_data'].get('iso_cert', False)
    return {'validation_status': cert}

def check_biocompatibility(state: SyringeState):
    bio_grade = state['spec_data'].get('material_grade')
    # Extended logic for medical grade materials
    return {'validation_status': state['validation_status'] and (bio_grade == 'medical')}

graph = StateGraph(SyringeState)
graph.add_node('validate_cert', validate_certification)
graph.add_node('check_material', check_biocompatibility)
graph.set_entry_point('validate_cert')
graph.add_edge('validate_cert', 'check_material')
graph.add_edge('check_material', END)
app = graph.compile()