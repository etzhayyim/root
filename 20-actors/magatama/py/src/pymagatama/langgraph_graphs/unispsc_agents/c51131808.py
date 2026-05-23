from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    quality_docs: List[str]
    compliance_check: bool

def validate_gmp(state: ProcurementState):
    state['compliance_check'] = all(doc in state['quality_docs'] for doc in ['COA', 'GMP_Cert'])
    print(f'Validating batch {state['batch_id']}: Compliance={state['compliance_check']}')
    return 'check_finished'

graph = StateGraph(ProcurementState)
graph.add_node('validate_gmp', validate_gmp)
graph.set_entry_point('validate_gmp')
graph.add_edge('validate_gmp', END)
compile_graph = graph.compile()
