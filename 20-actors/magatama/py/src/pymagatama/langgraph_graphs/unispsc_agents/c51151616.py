from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AtropineState(TypedDict):
    purity_level: float
    safety_check_passed: bool
    regulatory_docs: List[str]

def validate_purity(state: AtropineState):
    return {'safety_check_passed': state['purity_level'] >= 99.9}

def check_regulations(state: AtropineState):
    return {'regulatory_docs': ['FDA_APPROVAL', 'GMP_CERT']}

graph = StateGraph(AtropineState)
graph.add_node('purity', validate_purity)
graph.add_node('compliance', check_regulations)
graph.add_edge('purity', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('purity')
app = graph.compile()
