from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class HerbalState(TypedDict):
    batch_id: str
    quality_passed: bool
    compliance_docs: List[str]

def validate_compliance(state: HerbalState):
    state['quality_passed'] = all(doc in state['compliance_docs'] for doc in ['GMP', 'CoA'])
    print(f'Batch {state['batch_id']} compliance check: {state['quality_passed']}')
    return 'check_final'

graph = StateGraph(HerbalState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
