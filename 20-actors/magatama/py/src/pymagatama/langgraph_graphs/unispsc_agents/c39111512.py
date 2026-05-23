from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabLightState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_lighting_specs(state: LabLightState):
    specs = state['spec_data']
    is_compliant = (specs.get('CRI', 0) >= 90 and specs.get('IP_rating', 0) >= 20)
    return {'is_compliant': is_compliant}

def process_procurement(state: LabLightState):
    print('Procurement workflow for Bench Lights initialized')
    return state

graph = StateGraph(LabLightState)
graph.add_node('validate', validate_lighting_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
