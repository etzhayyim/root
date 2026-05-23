from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TileState(TypedDict):
    specs: dict
    approved: bool
    validation_log: List[str]

def validate_specs(state: TileState):
    log = []
    if state['specs'].get('water_absorption', 0) < 0.5:
        log.append('Porcelain grade verified')
    return {'validation_log': log}

def approval_node(state: TileState):
    return {'approved': len(state['validation_log']) > 0}

graph = StateGraph(TileState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
app = graph.compile()
