from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BenzbromaroneState(TypedDict):
    purity: float
    compliance_docs: List[str]
    is_approved: bool

def validate_quality(state: BenzbromaroneState):
    if state['purity'] >= 99.0:
        return {'is_approved': True}
    return {'is_approved': False}

def check_regulations(state: BenzbromaroneState):
    required = ['CoA', 'SafetyDataSheet']
    all_found = all(doc in state['compliance_docs'] for doc in required)
    return {'is_approved': state['is_approved'] and all_found}

graph = StateGraph(BenzbromaroneState)
graph.add_node('validate', validate_quality)
graph.add_node('compliance', check_regulations)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
