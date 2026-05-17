from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    material: str
    pressure_psi: float
    weld_certified: bool
    validation_passed: bool

def validate_specs(state: PipeState):
    if state['material'].startswith('Inconel') and state['weld_certified']:
        return {'validation_passed': True}
    return {'validation_passed': False}

graph = StateGraph(PipeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()