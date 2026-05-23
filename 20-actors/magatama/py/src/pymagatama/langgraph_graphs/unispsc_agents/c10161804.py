from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class LivestockState(TypedDict):
    supply_id: str
    validation_passed: bool
    log: Annotated[Sequence[str], operator.add]

def validate_supply(state: LivestockState):
    # Simulate validation of agricultural supply specs
    valid = state['supply_id'].startswith('LIV')
    return {'validation_passed': valid, 'log': [f'Validation result: {valid}']}

def process_inventory(state: LivestockState):
    if state['validation_passed']:
        return {'log': ['Supply processed and added to inventory']}
    return {'log': ['Supply rejected due to spec mismatch']}

graph = StateGraph(LivestockState)
graph.add_node('validate', validate_supply)
graph.add_node('process', process_inventory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
