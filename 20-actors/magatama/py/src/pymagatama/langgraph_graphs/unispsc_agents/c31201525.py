from typing import TypedDict
from langgraph.graph import StateGraph, END

class TapeState(TypedDict):
    spec_sheet: dict
    approved: bool
    validation_score: float

def validate_specs(state: TapeState):
    required = ['adhesive_strength', 'dielectric_voltage']
    scores = [state['spec_sheet'].get(key, 0) > 0 for key in required]
    return {'validation_score': 1.0 if all(scores) else 0.0}

def decision_node(state: TapeState):
    return {'approved': state['validation_score'] >= 1.0}

graph = StateGraph(TapeState)
graph.add_node('validate', validate_specs)
graph.add_node('decision', decision_node)
graph.add_edge('validate', 'decision')
graph.add_edge('decision', END)
graph.set_entry_point('validate')
graph = graph.compile()
