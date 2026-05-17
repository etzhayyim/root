from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RespiratorySetState(TypedDict):
    part_number: str
    is_sterile: bool
    compliance_docs: List[str]
    validation_result: bool

def validate_compliance(state: RespiratorySetState):
    state['validation_result'] = all(doc in state['compliance_docs'] for doc in ['ISO13485', 'CE_Mark'])
    print(f'Compliance validation: {state['validation_result']}')
    return state

def check_sterility(state: RespiratorySetState):
    state['is_sterile'] = True
    return state

graph = StateGraph(RespiratorySetState)
graph.add_node('compliance', validate_compliance)
graph.add_node('sterility', check_sterility)
graph.add_edge('compliance', 'sterility')
graph.add_edge('sterility', END)
graph.set_entry_point('compliance')
graph = graph.compile()