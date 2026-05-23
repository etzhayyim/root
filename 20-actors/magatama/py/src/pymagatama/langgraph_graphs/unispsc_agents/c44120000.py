from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OfficeSupplyState(TypedDict):
    items: List[str]
    validated_items: List[str]
    errors: List[str]

def validate_item(state: OfficeSupplyState):
    validated = [item for item in state['items'] if len(item) > 2]
    return {'validated_items': validated}

def check_inventory(state: OfficeSupplyState):
    print('Checking inventory levels for: ', state['validated_items'])
    return {'errors': []}

graph = StateGraph(OfficeSupplyState)
graph.add_node('validate', validate_item)
graph.add_node('inventory', check_inventory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inventory')
graph.add_edge('inventory', END)
graph = graph.compile()
