from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AntiviralState(TypedDict):
    drug_name: str
    regulatory_status: bool
    batch_compliance: bool

def validate_regulatory(state: AntiviralState):
    print(f'Validating regulatory status for {state['drug_name']}')
    return {'regulatory_status': True}

def check_batch(state: AntiviralState):
    print('Verifying batch and GMP data')
    return {'batch_compliance': True}

graph = StateGraph(AntiviralState)
graph.add_node('regulatory', validate_regulatory)
graph.add_node('batch', check_batch)
graph.add_edge('regulatory', 'batch')
graph.add_edge('batch', END)
graph.set_entry_point('regulatory')
graph = graph.compile()