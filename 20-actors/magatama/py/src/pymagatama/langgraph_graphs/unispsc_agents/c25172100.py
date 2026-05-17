from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SafetySystemState(TypedDict):
    part_id: str
    compliance_docs: List[str]
    validation_passed: bool

def validate_compliance(state: SafetySystemState):
    state['validation_passed'] = 'ISO_26262' in state['compliance_docs']
    return state

def run_security_protocol(state: SafetySystemState):
    print(f'Checking security encryption for: {state["part_id"]}')
    return state

graph = StateGraph(SafetySystemState)
graph.add_node('validate', validate_compliance)
graph.add_node('security', run_security_protocol)
graph.set_entry_point('validate')
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
app = graph.compile()