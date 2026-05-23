from typing import TypedDict
from langgraph.graph import StateGraph, END

class SeismicState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: SeismicState):
    required = ['frequency_range', 'gain_accuracy', 'noise_floor']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing critical calibration specs'}

workflow = StateGraph(SeismicState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
