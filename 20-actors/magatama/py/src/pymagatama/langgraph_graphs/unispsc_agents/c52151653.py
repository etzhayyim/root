from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class OysterKnifeState(TypedDict):
    specs: dict
    validation_results: list

def validate_materials(state: OysterKnifeState):
    blade = state['specs'].get('blade_material')
    if blade not in ['304_stainless', '420_stainless']:
        return {'validation_results': ['Invalid material specification']}
    return {'validation_results': ['Material verified']}

def process_procurement(state: OysterKnifeState):
    return {'validation_results': state['validation_results'] + ['Procurement approved']}

graph = StateGraph(OysterKnifeState)
graph.add_node('validate', validate_materials)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()