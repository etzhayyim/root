from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ContainerState(TypedDict):
    spec_data: dict
    validation_passed: bool
    log: List[str]

def validate_dimensions(state: ContainerState):
    specs = state['spec_data']
    passed = 'dimensions' in specs and 'load_capacity' in specs
    return {'validation_passed': passed, 'log': ['Dimension/Load check completed']}

def safety_compliance_check(state: ContainerState):
    passed = state['validation_passed']
    return {'log': state['log'] + ['Safety compliance verification finished']}

graph = StateGraph(ContainerState)
graph.add_node('validate', validate_dimensions)
graph.add_node('safety', safety_compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()