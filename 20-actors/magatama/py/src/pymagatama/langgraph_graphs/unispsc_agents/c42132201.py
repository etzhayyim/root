from typing import TypedDict, List
from langgraph.graph import StateGraph, END
class DispenserState(TypedDict):
    specs: dict
    validated: bool
    errors: List[str]
def validate_specs(state: DispenserState):
    errors = []
    if 'material' not in state['specs']: errors.append('Missing material spec')
    return {'validated': len(errors) == 0, 'errors': errors}
def finalize_procurement(state: DispenserState):
    return {'validated': True}
graph = StateGraph(DispenserState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
