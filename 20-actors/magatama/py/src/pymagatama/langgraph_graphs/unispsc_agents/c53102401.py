from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StockingState(TypedDict):
    material: str
    compression_level: str
    is_compliant: bool
    log: List[str]

def validate_specs(state: StockingState):
    compliant = state['material'] in ['Nylon', 'Spandex', 'Cotton']
    return {'is_compliant': compliant, 'log': ['Material validated']}

def check_compression(state: StockingState):
    is_ok = int(state['compression_level'].replace('mmHg', '')) > 0
    return {'is_compliant': is_ok, 'log': ['Compression check passed']}

graph = StateGraph(StockingState)
graph.add_node('validate', validate_specs)
graph.add_node('compression', check_compression)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compression')
graph.add_edge('compression', END)
graph = graph.compile()