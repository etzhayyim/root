from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AnimalFeedState(TypedDict):
    batch_id: str
    purity_validated: bool
    compliance_cleared: bool
    inspection_log: List[str]

def validate_purity(state: AnimalFeedState):
    print(f'Validating purity for {state["batch_id"]}')
    return {'purity_validated': True, 'inspection_log': ['Purity test passed']}

def check_regulations(state: AnimalFeedState):
    print(f'Checking regulatory compliance for {state["batch_id"]}')
    return {'compliance_cleared': True, 'inspection_log': state['inspection_log'] + ['Compliance verified']}

graph = StateGraph(AnimalFeedState)
graph.add_node('purity_check', validate_purity)
graph.add_node('regulatory_check', check_regulations)
graph.add_edge('purity_check', 'regulatory_check')
graph.add_edge('regulatory_check', END)
graph.set_entry_point('purity_check')
compiled_graph = graph.compile()
