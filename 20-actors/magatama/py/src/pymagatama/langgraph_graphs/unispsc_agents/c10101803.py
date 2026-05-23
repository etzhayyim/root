from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SeedProcurementState(TypedDict):
    seed_type: str
    germination_rate: float
    phytosanitary_docs: bool
    validation_log: List[str]

def validate_seed_data(state: SeedProcurementState):
    log = []
    if state['germination_rate'] < 0.85:
        log.append('Low germination rate detected')
    if not state['phytosanitary_docs']:
        log.append('Missing phytosanitary documentation')
    return {'validation_log': log}

def process_procurement(state: SeedProcurementState):
    if state['validation_log']:
        return 'REJECTED'
    return 'APPROVED'

graph = StateGraph(SeedProcurementState)
graph.add_node('validate', validate_seed_data)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)

compiled_graph = graph.compile()
