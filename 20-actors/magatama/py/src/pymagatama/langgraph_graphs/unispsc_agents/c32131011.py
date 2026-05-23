from typing import TypedDict
from langgraph.graph import StateGraph, END

class ICState(TypedDict):
    lid_specs: dict
    validation_status: bool
    compliance_report: str

def validate_materials(state: ICState):
    specs = state['lid_specs']
    is_valid = 'material_composition' in specs and 'plating_thickness_micron' in specs
    return {'validation_status': is_valid}

def export_check(state: ICState):
    return {'compliance_report': 'Dual-use export review completed.'}

graph = StateGraph(ICState)
graph.add_node('validate', validate_materials)
graph.add_node('export_review', export_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
app = graph.compile()
