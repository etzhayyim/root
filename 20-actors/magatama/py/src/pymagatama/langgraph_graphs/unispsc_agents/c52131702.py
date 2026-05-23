from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CurtainRodState(TypedDict):
    specifications: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: CurtainRodState):
    errors = []
    if 'weight_capacity' not in state['specifications']:
        errors.append('Weight capacity missing')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

graph = StateGraph(CurtainRodState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
