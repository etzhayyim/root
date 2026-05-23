from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ClinicProcurementState(TypedDict):
    facility_requirements: List[str]
    compliance_check: bool
    final_approval: bool

def validate_facility_specs(state: ClinicProcurementState):
    print('Validating clinical facility specifications...')
    state['compliance_check'] = len(state['facility_requirements']) > 0
    return state

def run_procurement_workflow(state: ClinicProcurementState):
    print('Initiating clinical equipment procurement workflow...')
    state['final_approval'] = True
    return state

graph = StateGraph(ClinicProcurementState)
graph.add_node('validate', validate_facility_specs)
graph.add_node('procure', run_procurement_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'procure')
graph.add_edge('procure', END)
graph = graph.compile()
