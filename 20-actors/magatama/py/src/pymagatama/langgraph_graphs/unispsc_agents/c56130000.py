from typing import TypedDict
from langgraph.graph import StateGraph, END

class MerchGraphState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: MerchGraphState):
    fields = ['Material', 'LoadCapacity']
    errors = [f for f in fields if f not in state['spec_data']]
    return {'validated': len(errors) == 0, 'error_log': errors}

def finalize_order(state: MerchGraphState):
    return {'error_log': ['Order ready for procurement']}

graph = StateGraph(MerchGraphState)
graph.add_node('validate', validate_specs)
graph.add_node('finish', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finish')
graph.add_edge('finish', END)
graph.compile()
