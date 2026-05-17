from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class PipetteState(TypedDict):
    specs: dict
    validation_passed: bool
    errors: List[str]
def validate_specs(state: PipetteState):
    required = ['Volume Accuracy', 'Calibration Certificate']
    errors = [f'{key} missing' for key in required if key not in state['specs']]
    return {'validation_passed': len(errors) == 0, 'errors': errors}
def finalize(state: PipetteState):
    return {'validation_passed': True}
graph = StateGraph(PipetteState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()