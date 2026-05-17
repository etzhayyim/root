from typing import TypedDict
from langgraph.graph import StateGraph, END

class SatelliteState(TypedDict):
    specs: dict
    validation_checks: list
    governance_cleared: bool

def validate_tech(state: SatelliteState):
    checks = [k for k in ['Radiation', 'Payload'] if k in state['specs']]
    return {'validation_checks': checks}

def check_compliance(state: SatelliteState):
    return {'governance_cleared': state.get('export_permit', False)}

graph = StateGraph(SatelliteState)
graph.add_node('tech_spec', validate_tech)
graph.add_node('export_check', check_compliance)
graph.set_entry_point('tech_spec')
graph.add_edge('tech_spec', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()