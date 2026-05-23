from typing import TypedDict
from langgraph.graph import StateGraph, END

class LysateState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_lysate_specs(state: LysateState):
    specs = state['spec_data']
    required = ['purity_percentage', 'storage_temperature_requirement']
    passed = all(k in specs for k in required) and specs.get('purity_percentage', 0) > 90
    return {'validation_passed': passed, 'compliance_report': 'Validated' if passed else 'Failed QC'}

def check_cold_chain(state: LysateState):
    # Simulate cold chain logic
    return {'compliance_report': state['compliance_report'] + '; Cold chain verified.'}

graph = StateGraph(LysateState)
graph.add_node('validate', validate_lysate_specs)
graph.add_node('cold_chain', check_cold_chain)
graph.add_edge('validate', 'cold_chain')
graph.add_edge('cold_chain', END)
graph.set_entry_point('validate')
app = graph.compile()
