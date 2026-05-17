from langgraph.graph import StateGraph, END
from typing import TypedDict

class SealingWaxState(TypedDict):
    spec_data: dict
    validated: bool

def validate_wax_props(state: SealingWaxState):
    props = state.get('spec_data', {})
    is_valid = props.get('melting_point') > 60 and props.get('non_toxic') is True
    return {'validated': is_valid}

def process_procurement(state: SealingWaxState):
    return {'validated': state['validated']}

graph = StateGraph(SealingWaxState)
graph.add_node('validate', validate_wax_props)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
app = graph.compile()