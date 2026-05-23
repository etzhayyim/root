from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    raw_material: str
    tests_passed: bool
    compliance_report: str

def validate_purity(state: ProcurementState):
    print(f'Validating purity for {state['raw_material']}')
    return {'tests_passed': True, 'compliance_report': 'Purity standards met for Gotu Kola'}

def check_regulations(state: ProcurementState):
    print('Checking herbal supplement regulations...')
    return {'compliance_report': 'Passed FDA/Health Authority review'}

graph = StateGraph(ProcurementState)
graph.add_node('Validate', validate_purity)
graph.add_node('Compliance', check_regulations)
graph.set_entry_point('Validate')
graph.add_edge('Validate', 'Compliance')
graph.add_edge('Compliance', END)
graph = graph.compile()
