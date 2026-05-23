from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class HydraulicState(TypedDict):
    spec_sheet_id: str
    pressure_validated: bool
    compliance_passed: bool
    workflow_log: List[str]

def validate_technical_specs(state: HydraulicState):
    # Simulate CAD/Spec validation for Hydraulic Cylinders
    state['pressure_validated'] = True
    state['workflow_log'].append('Validation: Technical specs and pressure ratings verified.')
    return state

def check_regulatory_compliance(state: HydraulicState):
    # Simulate Export Control and Safety checks
    state['compliance_passed'] = True
    state['workflow_log'].append('Compliance: Dual-use export control checks completed.')
    return state

graph = StateGraph(HydraulicState)
graph.add_node('validate', validate_technical_specs)
graph.add_node('compliance', check_regulatory_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

# Compile the graph
app = graph.compile()
