from typing import TypedDict
from langgraph.graph import StateGraph, END

class ThicknessState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: ThicknessState):
    specs = state['spec_data']
    errors = []
    if specs.get('accuracy_tolerance_pct', 0) > 0.05: errors.append('Tolerance too loose')
    return {'validated': len(errors) == 0, 'error_log': errors}

graph = StateGraph(ThicknessState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
