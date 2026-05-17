from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    gmp_status: bool
    purity_level: float
    compliance_checks: List[str]

def validate_gmp(state: ProcurementState):
    print(f'Checking GMP for {state[\'material_name\']}')
    return {'compliance_checks': ['GMP_CERTIFIED'] if state['gmp_status'] else ['GMP_FAILED']}

def validate_purity(state: ProcurementState):
    print(f'Verifying purity: {state[\'purity_level\']}%')
    status = 'VALID' if state['purity_level'] >= 99.0 else 'REJECTED'
    return {'compliance_checks': state['compliance_checks'] + [status]}

graph = StateGraph(ProcurementState)
graph.add_node('gmp', validate_gmp)
graph.add_node('purity', validate_purity)
graph.set_entry_point('gmp')
graph.add_edge('gmp', 'purity')
graph.add_edge('purity', END)
graph = graph.compile()