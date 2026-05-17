from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeldingGearState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_report: str

def validate_specs(state: WeldingGearState):
    required = ['ANSI_rating', 'shade_level']
    all_present = all(k in state['spec_data'] for k in required)
    return {'validated': all_present, 'compliance_report': 'Passed' if all_present else 'Missing critical fields'}

def process_procurement(state: WeldingGearState):
    if state['validated']:
        print('Proceeding with procurement order')
    return {'compliance_report': 'Order ready for dispatch'}

graph = StateGraph(WeldingGearState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
app = graph.compile()