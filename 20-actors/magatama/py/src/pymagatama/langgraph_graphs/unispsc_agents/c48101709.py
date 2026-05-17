from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DispenserState(TypedDict):
    spec_sheet: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: DispenserState):
    errors = []
    if 'NSF_cert' not in state['spec_sheet']: errors.append('NSF certification missing')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(DispenserState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()