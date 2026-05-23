from langgraph.graph import StateGraph, END
from typing import TypedDict

class BioState(TypedDict):
    material_name: str
    purity_level: float
    storage_temp: str
    is_sterile: bool

def validate_purity(state: BioState):
    if state['purity_level'] < 0.99:
        raise ValueError('Purity below 99% for S. pombe media additive')
    return 'VALIDATED'

def check_cold_chain(state: BioState):
    if state['storage_temp'] not in ['-20C', '4C']:
        return 'FLAG_TEMP_RISK'
    return 'READY'

graph = StateGraph(BioState)
graph.add_node('purity_check', validate_purity)
graph.add_node('cold_chain', check_cold_chain)
graph.set_entry_point('purity_check')
graph.add_edge('purity_check', 'cold_chain')
graph.add_edge('cold_chain', END)
graph = graph.compile()
