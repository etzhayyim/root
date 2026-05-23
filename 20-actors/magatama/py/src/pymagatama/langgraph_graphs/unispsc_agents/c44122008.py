from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class IndexState(TypedDict):
    spec_sheet: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: IndexState):
    errors = []
    if 'material' not in state['spec_sheet']: errors.append('Missing material')
    if 'size' not in state['spec_sheet']: errors.append('Missing sheet dimensions')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(IndexState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
