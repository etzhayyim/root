from typing import TypedDict
from langgraph.graph import StateGraph, END

class GeneratorState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_score: float

def validate_specs(state: GeneratorState):
    valid = state['spec_data'].get('nominal_output_w', 0) > 0
    return {'validation_passed': valid}

def safety_check(state: GeneratorState):
    score = 1.0 if 'UN38.3' in state['spec_data'].get('certs', []) else 0.5
    return {'compliance_score': score}

graph = StateGraph(GeneratorState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
compiled_graph = graph.compile()