from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RubberState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_rubber_specs(state: RubberState):
    errors = []
    required = ['hardness', 'material', 'thickness']
    for field in required:
        if field not in state['specifications']:
            errors.append(f'Missing {field}')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(RubberState)
graph.add_node('validate', validate_rubber_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()