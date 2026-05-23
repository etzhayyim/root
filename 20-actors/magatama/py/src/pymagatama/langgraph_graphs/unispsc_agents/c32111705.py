from typing import TypedDict
from langgraph.graph import StateGraph, END
class OptoState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_report: str
def validate_specs(state: OptoState):
    if state['spec_data'].get('Isolation Voltage', 0) >= 5000:
        return {'validated': True, 'compliance_report': 'High voltage isolation confirmed'}
    return {'validated': False, 'compliance_report': 'Isolation voltage below safety threshold'}
def route_step(state: OptoState):
    return 'validate' if state.get('spec_data') else 'end'
graph = StateGraph(OptoState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
