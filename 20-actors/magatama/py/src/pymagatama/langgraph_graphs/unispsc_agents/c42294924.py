from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class InstrumentState(TypedDict):
    instrument_id: str
    compliance_docs: List[str]
    is_verified: bool

def validate_compliance(state: InstrumentState):
    state['is_verified'] = all(['certificate' in doc for doc in state['compliance_docs']])
    return state

def inspection_step(state: InstrumentState):
    print(f"Inspecting instrument: {state['instrument_id']}")
    return {'is_verified': True}

graph = StateGraph(InstrumentState)
graph.add_node("validate", validate_compliance)
graph.add_node("inspect", inspection_step)
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph.set_entry_point("validate")
graph = graph.compile()
