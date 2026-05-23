from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MathKitState(TypedDict):
    kit_contents: List[str]
    compliance_certified: bool
    validation_errors: List[str]

def validate_kit_contents(state: MathKitState):
    required = ['geometry_set', 'calculator', 'graphing_tools']
    errors = []
    for item in required:
        if item not in state['kit_contents']:
            errors.append(f'Missing {item}')
    return {'validation_errors': errors, 'compliance_certified': len(errors) == 0}

graph = StateGraph(MathKitState)
graph.add_node('validate', validate_kit_contents)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
