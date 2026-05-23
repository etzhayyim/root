from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EngineState(TypedDict):
    part_number: str
    compliance_docs: List[str]
    approved: bool

def validate_compliance(state: EngineState):
    required = ['AS9100', 'StressTest', 'MaterialCert']
    state['approved'] = all(doc in state['compliance_docs'] for doc in required)
    return state

def route_verification(state: EngineState):
    return 'process' if state['approved'] else END

graph = StateGraph(EngineState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
