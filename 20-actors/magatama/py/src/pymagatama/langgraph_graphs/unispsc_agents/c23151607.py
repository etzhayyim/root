from typing import TypedDict
from langgraph.graph import StateGraph, END

class CompressorState(TypedDict):
    specs: dict
    validation_errors: list
    is_approved: bool

def validate_specs(state: CompressorState):
    errors = []
    if state['specs'].get('max_pressure_psi', 0) > 150:
        errors.append('Pressure exceeds standard safety threshold')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(CompressorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compiled_graph = graph.compile()