from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScraperState(TypedDict):
    blade_type: str
    material_certified: bool
    safety_check: bool

def validate_blade(state: ScraperState):
    return {'material_certified': state['blade_type'] in ['stainless_steel', 'carbon_steel']}

def safety_assessment(state: ScraperState):
    return {'safety_check': True}

graph = StateGraph(ScraperState)
graph.add_node('validate', validate_blade)
graph.add_node('safety', safety_assessment)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
