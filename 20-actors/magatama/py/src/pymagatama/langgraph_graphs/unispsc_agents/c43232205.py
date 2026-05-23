from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FontState(TypedDict):
    font_files: List[str]
    license_type: str
    validation_errors: List[str]
    approved: bool

def validate_font_format(state: FontState):
    errors = []
    for f in state['font_files']:
        if not f.endswith(('.otf', '.ttf', '.woff2')):
            errors.append(f'Invalid format: {f}')
    return {'validation_errors': errors}

def check_license(state: FontState):
    if state['license_type'] not in ['EULA', 'Corporate', 'OpenSource']:
        return {'approved': False}
    return {'approved': True}

graph = StateGraph(FontState)
graph.add_node('validate', validate_font_format)
graph.add_node('license', check_license)
graph.set_entry_point('validate')
graph.add_edge('validate', 'license')
graph.add_edge('license', END)
graph = graph.compile()
