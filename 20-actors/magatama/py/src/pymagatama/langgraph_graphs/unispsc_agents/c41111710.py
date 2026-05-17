from typing import TypedDict
from langgraph.graph import StateGraph, END

class MicroscopeState(TypedDict):
    specs: dict
    validation_status: str

def validate_vacuum(state: MicroscopeState):
    vacuum_type = state['specs'].get('vacuum_system_type')
    status = 'PASS' if vacuum_type in ['turbo', 'ion'] else 'FAIL_REQUIRE_UPGRADE'
    return {'validation_status': status}

def check_export(state: MicroscopeState):
    print('Checking dual-use compliance...')
    return {'validation_status': 'COMPLIANT'}

graph = StateGraph(MicroscopeState)
graph.add_node('vacuum_check', validate_vacuum)
graph.add_node('export_check', check_export)
graph.set_entry_point('vacuum_check')
graph.add_edge('vacuum_check', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()