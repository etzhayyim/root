from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class AutopsySawState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]
def validate_specs(state: AutopsySawState):
    errors = []
    if 'sterilization_type' not in state['spec_data']:
        errors.append('Missing sterilization requirement.')
    return {'validation_passed': len(errors) == 0, 'errors': errors}
def analyze_risk(state: AutopsySawState):
    print('Assessing biohazard and electrical safety for clinical deployment...')
    return {'validation_passed': state['validation_passed']}
graph = StateGraph(AutopsySawState)
graph.add_node('validate', validate_specs)
graph.add_node('risk_analysis', analyze_risk)
graph.set_entry_point('validate')
graph.add_edge('validate', 'risk_analysis')
graph.add_edge('risk_analysis', END)
graph = graph.compile()