from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DentalToolState(TypedDict):
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: DentalToolState):
    required = ['material_cert', 'iso_13485']
    missing = [f for f in required if f not in state['specs']]
    state['validation_passed'] = len(missing) == 0
    state['errors'] = missing
    return 'end'

graph = StateGraph(DentalToolState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
