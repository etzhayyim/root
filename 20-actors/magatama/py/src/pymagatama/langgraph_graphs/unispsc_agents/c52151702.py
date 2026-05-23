from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KitchenKnifeState(TypedDict):
    material: str
    hardness: int
    safety_cert: bool
    validation_log: List[str]

def validate_specs(state: KitchenKnifeState):
    log = []
    if state['hardness'] < 50: log.append('Low hardness failing durability')
    if not state['safety_cert']: log.append('Missing food contact certification')
    return {'validation_log': log}

def route_by_validation(state: KitchenKnifeState):
    return 'APPROVED' if not state['validation_log'] else 'REJECTED'

graph = StateGraph(KitchenKnifeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
