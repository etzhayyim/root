from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MineralState(TypedDict):
    purity: float
    origin: str
    compliance_docs: List[str]
    validation_passed: bool

def validate_purity(state: MineralState):
    passed = state['purity'] >= 99.5
    return {'validation_passed': passed}

def check_compliance(state: MineralState):
    has_docs = len(state['compliance_docs']) >= 3
    return {'validation_passed': state['validation_passed'] and has_docs}

graph = StateGraph(MineralState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
