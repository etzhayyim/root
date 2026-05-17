from typing import TypedDict
from langgraph.graph import StateGraph, END
class BiopsyState(TypedDict):
    specs: dict
    is_validated: bool
def validate_trephine(state: BiopsyState):
    required = ['material', 'sterilization', 'diameter']
    valid = all(k in state['specs'] for k in required)
    return {'is_validated': valid}
def check_compliance(state: BiopsyState):
    print('Checking regulatory compliance for medical device...')
    return {'is_validated': state['is_validated']}
graph = StateGraph(BiopsyState)
graph.add_node('validate', validate_trephine)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()