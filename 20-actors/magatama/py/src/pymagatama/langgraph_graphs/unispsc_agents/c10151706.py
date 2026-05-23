from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class SeedIngestState(TypedDict):
    seed_metadata: dict
    validation_reports: List[str]
    approved: bool

def validate_seed_quality(state: SeedIngestState):
    seed = state['seed_metadata']
    if seed.get('germination_rate', 0) > 85:
        return {'validation_reports': ['Quality check passed'], 'approved': True}
    return {'validation_reports': ['Quality check failed'], 'approved': False}

def update_inventory(state: SeedIngestState):
    return {'validation_reports': state['validation_reports'] + ['Inventory updated']}

graph = StateGraph(SeedIngestState)
graph.add_node('validate', validate_seed_quality)
graph.add_node('inventory', update_inventory)
graph.add_edge('validate', 'inventory')
graph.add_edge('inventory', END)
graph.set_entry_point('validate')
graph = graph.compile()
