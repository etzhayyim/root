from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EchinaceaState(TypedDict):
    batch_id: str
    purity_cert: bool
    microbial_test: bool
    status: str

def validate_quality(state: EchinaceaState):
    if state['purity_cert'] and state['microbial_test']:
        return {'status': 'APPROVED'}
    return {'status': 'REJECTED'}

workflow = StateGraph(EchinaceaState)
workflow.add_node('validation', validate_quality)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()