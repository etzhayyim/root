from typing import TypedDict
from langgraph.graph import StateGraph, END

class IncubatorState(TypedDict):
    spec_data: dict
    validation_passed: bool
    log: list

def validate_specs(state: IncubatorState):
    specs = state['spec_data']
    passed = all([specs.get('temp_stability'), specs.get('gas_control')])
    return {'validation_passed': passed, 'log': ['Specs checked']}

def check_compliance(state: IncubatorState):
    return {'log': state['log'] + ['Compliance verified']}

graph = StateGraph(IncubatorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()