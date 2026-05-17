from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MachineSpecs(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: MachineSpecs):
    errors = []
    if state['specs'].get('spindle_speed', 0) < 1000:
        errors.append('Spindle speed below industrial requirement.')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(MachineSpecs)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()