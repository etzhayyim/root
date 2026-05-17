from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalTableState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_specs(state: SurgicalTableState):
    required = ['Load Capacity', 'IEC 60601']
    results = [key in state['spec_data'] for key in required]
    is_valid = all(results)
    return {'validation_results': results, 'is_compliant': is_valid}

def clinical_compliance_check(state: SurgicalTableState):
    print('Running specialized medical device compliance audit...')
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(SurgicalTableState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', clinical_compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()