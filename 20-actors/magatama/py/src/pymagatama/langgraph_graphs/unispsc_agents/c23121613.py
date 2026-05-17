from typing import TypedDict
from langgraph.graph import StateGraph, END

class CompressorState(TypedDict):
    spec_data: dict
    validation_report: dict
    is_compliant: bool

def validate_specs(state: CompressorState):
    specs = state['spec_data']
    valid = specs.get('pressure', 0) > 0 and 'cert' in specs
    return {'validation_report': {'status': 'success' if valid else 'failed'}, 'is_compliant': valid}

graph = StateGraph(CompressorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()