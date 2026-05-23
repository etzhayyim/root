from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class IonImplanterState(TypedDict):
    specs: dict
    approved: bool
    validation_log: List[str]

def validate_vacuum(state: IonImplanterState):
    vacuum = state['specs'].get('vacuum_level')
    is_ok = vacuum < 1e-7
    return {'validation_log': [f'Vacuum Check: {is_ok}']}

def validate_export(state: IonImplanterState):
    license_ok = state['specs'].get('has_export_license', False)
    return {'approved': license_ok, 'validation_log': ['Export Check Passed']}

graph = StateGraph(IonImplanterState)
graph.add_node('vacuum_check', validate_vacuum)
graph.add_node('export_check', validate_export)
graph.set_entry_point('vacuum_check')
graph.add_edge('vacuum_check', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
