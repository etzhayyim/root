from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CoalProcurementState(TypedDict):
    commodity_code: str
    spec_compliance: bool
    safety_check_passed: bool
    log: List[str]

def validate_specs(state: CoalProcurementState) -> CoalProcurementState:
    state['log'].append('Validating coal caloric and impurity specs...')
    state['spec_compliance'] = True
    return state

def safety_audit(state: CoalProcurementState) -> CoalProcurementState:
    state['log'].append('Performing safety/environmental audit...')
    state['safety_check_passed'] = True
    return state

graph = StateGraph(CoalProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_audit)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)

graph = graph.compile()