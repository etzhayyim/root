from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ElectricalSpecState(TypedDict):
    part_number: str
    specifications: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: ElectricalSpecState):
    specs = state['specifications']
    errors = []
    if 'voltage' not in specs or specs['voltage'] <= 0:
        errors.append('Invalid voltage rating')
    state['validation_passed'] = len(errors) == 0
    state['errors'] = errors
    return state

graph = StateGraph(ElectricalSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
