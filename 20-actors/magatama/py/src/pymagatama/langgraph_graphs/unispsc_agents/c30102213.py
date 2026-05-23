from typing import TypedDict
from langgraph.graph import StateGraph, END

class TinPlateState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: TinPlateState):
    required = ['thickness', 'coating_weight', 'temper']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

graph = StateGraph(TinPlateState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
