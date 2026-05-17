from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BarbellState(TypedDict):
    specs: dict
    validation_log: List[str]
    approved: bool

def validate_specs(state: BarbellState):
    log = []
    if state['specs'].get('tensile_strength', 0) < 150000:
        log.append('Tensile strength below commercial standard.')
    return {'validation_log': log, 'approved': len(log) == 0}

graph = StateGraph(BarbellState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()