from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ToolSpec(TypedDict):
    specs: dict
    is_validated: bool
    validation_errors: List[str]

def validate_bolt_cutter(state: ToolSpec):
    errors = []
    if state['specs'].get('hrc', 0) < 50:
        errors.append('Blade hardness insufficient for industrial use.')
    return {'is_validated': len(errors) == 0, 'validation_errors': errors}

graph = StateGraph(ToolSpec)
graph.add_node('validate', validate_bolt_cutter)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()