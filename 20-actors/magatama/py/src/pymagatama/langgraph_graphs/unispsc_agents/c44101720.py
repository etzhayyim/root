from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FontProcurementState(TypedDict):
    font_format: str
    license_type: str
    validation_errors: List[str]

def validate_font_specs(state: FontProcurementState):
    errors = []
    if state['font_format'] not in ['OTF', 'TTF', 'WOFF2']:
        errors.append('Unsupported font format.')
    return {'validation_errors': errors}

def check_license_compliance(state: FontProcurementState):
    if state['license_type'] == 'restricted':
        return {'validation_errors': state['validation_errors'] + ['Restricted license requires legal review']}
    return {'validation_errors': state['validation_errors']}

graph = StateGraph(FontProcurementState)
graph.add_node('validate', validate_font_specs)
graph.add_node('license_check', check_license_compliance)
graph.add_edge('validate', 'license_check')
graph.add_edge('license_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
