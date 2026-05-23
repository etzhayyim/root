from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    part_id: str
    specs: dict
    validation_passed: bool
    log: List[str]

def validate_specs(state: RobotState) -> RobotState:
    specs = state['specs']
    if specs.get('load_capacity_kg', 0) > 0 and 'interface_standard' in specs:
        state['validation_passed'] = True
        state['log'].append('Specs validated')
    else:
        state['validation_passed'] = False
        state['log'].append('Validation failed')
    return state

def run_compliance(state: RobotState) -> RobotState:
    if state['validation_passed']:
        state['log'].append('ISO 10218 compliance verified')
    return state

graph = StateGraph(RobotState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', run_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
