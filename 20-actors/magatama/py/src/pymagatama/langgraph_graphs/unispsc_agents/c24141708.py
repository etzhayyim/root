from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ParcelHandleState(TypedDict):
    load_capacity_kg: float
    material: str
    is_compliant: bool
    validation_log: List[str]

def validate_load_capacity(state: ParcelHandleState):
    limit = 25.0
    if state['load_capacity_kg'] > limit:
        state['validation_log'].append(f'Overloaded capacity detected: {state['load_capacity_kg']}kg')
        return {'is_compliant': False}
    return {'is_compliant': True}

def final_check(state: ParcelHandleState):
    return {'validation_log': state['validation_log'] + ['Final safety check passed']}

graph = StateGraph(ParcelHandleState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('finish', final_check)
graph.add_edge('validate', 'finish')
graph.add_edge('finish', END)
graph.set_entry_point('validate')
graph = graph.compile()