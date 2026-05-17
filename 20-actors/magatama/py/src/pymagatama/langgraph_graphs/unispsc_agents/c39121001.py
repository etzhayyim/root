from typing import TypedDict
from langgraph.graph import StateGraph, END

class TransformerState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_efficiency(state: TransformerState):
    spec = state['spec_data']
    valid = spec.get('efficiency_standard_compliance') == 'DOE_2016'
    return {'validation_results': [f'Efficiency check: {valid}']}

def check_safety_ratings(state: TransformerState):
    # Simulate complex safety regulation validation
    is_safe = state['spec_data'].get('insulation_class') in ['H', 'F']
    return {'is_approved': is_safe}

graph = StateGraph(TransformerState)
graph.add_node('efficiency', validate_efficiency)
graph.add_node('safety', check_safety_ratings)
graph.set_entry_point('efficiency')
graph.add_edge('efficiency', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()