from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WallpaperToolState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_tool_specs(state: WallpaperToolState):
    errors = []
    if not state['specs'].get('roller_material'):
        errors.append('Missing roller material specification')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(WallpaperToolState)
graph.add_node('validate', validate_tool_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()