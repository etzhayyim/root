from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BallscrewState(TypedDict):
    spec_data: dict
    validation_passed: bool
    is_controlled_goods: bool

def validate_specs(state: BallscrewState):
    specs = state['spec_data']
    passed = all(k in specs for k in ['lead', 'accuracy_grade'])
    print(f'Validating specs: {specs}')
    return {'validation_passed': passed}

def export_check(state: BallscrewState):
    is_controlled = state['spec_data'].get('accuracy_grade') == 'C0'
    return {'is_controlled_goods': is_controlled}

graph = StateGraph(BallscrewState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', export_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
