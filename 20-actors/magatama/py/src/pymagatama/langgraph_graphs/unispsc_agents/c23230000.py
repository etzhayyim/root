from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ToolingState(TypedDict):
    tool_specs: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: ToolingState):
    hardness = state['tool_specs'].get('hardness_hrc', 0)
    if hardness < 40:
        return {'validation_passed': False, 'errors': ['Hardness below industrial minimum']}
    return {'validation_passed': True}

def route_by_validation(state: ToolingState):
    return 'valid' if state['validation_passed'] else 'invalid'

graph = StateGraph(ToolingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
