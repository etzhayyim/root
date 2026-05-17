from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ToasterState(TypedDict):
    model_id: str
    safety_check_passed: bool
    specs: dict

def validate_specs(state: ToasterState):
    required = ['voltage', 'certification', 'wattage']
    passed = all(k in state['specs'] for k in required)
    return {'safety_check_passed': passed}

def perform_safety_review(state: ToasterState):
    print(f'Performing safety audit for {state['model_id']}')
    return {'safety_check_passed': True}

graph = StateGraph(ToasterState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', perform_safety_review)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()