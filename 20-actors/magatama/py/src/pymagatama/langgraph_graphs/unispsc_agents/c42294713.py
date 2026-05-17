from typing import TypedDict
from langgraph.graph import StateGraph, END

class PerfusionState(TypedDict):
    device_id: str
    compliance_docs: list[str]
    approved: bool

def validate_certification(state: PerfusionState):
    state['approved'] = all(doc in state['compliance_docs'] for doc in ['ISO-13485', 'FDA-510k'])
    print(f'Validation result for {state['device_id']}: {state['approved']}')
    return 'end'

graph = StateGraph(PerfusionState)
graph.add_node('validate', validate_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()