from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CompostState(TypedDict):
    batch_id: str
    nutrient_profile: dict
    status: str
    validation_logs: List[str]

def validate_nutrient_composition(state: CompostState) -> CompostState:
    n = state.get('nutrient_profile', {}).get('nitrogen', 0)
    if n < 1.5:
        state['status'] = 'REJECTED_LOW_NUTRIENT'
        state['validation_logs'].append('Nitrogen level below 1.5% threshold.')
    else:
        state['status'] = 'VALIDATED'
        state['validation_logs'].append('Nutrient profile verified.')
    return state

def check_pathogen_risk(state: CompostState) -> CompostState:
    if state['status'] != 'VALIDATED':
        return state
    state['validation_logs'].append('Pathogen analysis cleared.')
    return state

graph = StateGraph(CompostState)
graph.add_node('validate', validate_nutrient_composition)
graph.add_node('pathogen_check', check_pathogen_risk)
graph.add_edge('validate', 'pathogen_check')
graph.add_edge('pathogen_check', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
