from typing import TypedDict, List
from langgraph.graph import StateGraph, END
class MillingMachineState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool
def validate_specs(state: MillingMachineState):
    errors = []
    if state['specs'].get('precision', 0) > 0.05:
        errors.append('Precision tolerance is outside acceptable industrial limits.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}
def finalize_procurement(state: MillingMachineState):
    print('Proceeding with procurement workflow for validated milling machinery.')
    return {}
graph = StateGraph(MillingMachineState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()