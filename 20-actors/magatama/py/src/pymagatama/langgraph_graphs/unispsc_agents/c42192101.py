from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PhlebotomySpecState(TypedDict):
    item_id: str
    specs: dict
    approved: bool
    validation_log: List[str]

def validate_specs(state: PhlebotomySpecState):
    log = []
    if state['specs'].get('WeightCapacity', 0) < 150:
        log.append('Weight capacity insufficient for standard medical chair safety.')
    return {'validation_log': log, 'approved': len(log) == 0}

def graph_nodes():
    builder = StateGraph(PhlebotomySpecState)
    builder.add_node('validate', validate_specs)
    builder.set_entry_point('validate')
    builder.add_edge('validate', END)
    return builder.compile()

graph = graph_nodes()