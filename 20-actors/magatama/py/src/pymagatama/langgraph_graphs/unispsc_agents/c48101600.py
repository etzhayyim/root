from langgraph.graph import StateGraph, END
from typing import TypedDict
class FoodPrepState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_score: float
def validate_specs(state: FoodPrepState):
    required = ['SUS304', 'NSF_certified']
    state['validated'] = all(k in state['spec_data'] for k in required)
    return state
def check_compliance(state: FoodPrepState):
    state['compliance_score'] = 1.0 if state['validated'] else 0.0
    return state
graph = StateGraph(FoodPrepState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
