from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoodProcessorState(TypedDict):
    model_name: str
    spec_check: bool
    safety_verified: bool

def validate_specs(state: FoodProcessorState):
    print(f'Validating specs for {state[\'model_name\']}')
    return {'spec_check': True}

def verify_safety(state: FoodProcessorState):
    print('Running blade and electrical safety protocols')
    return {'safety_verified': True}

graph = StateGraph(FoodProcessorState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', verify_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()