from typing import TypedDict
from langgraph.graph import StateGraph, END

class MagnetState(TypedDict):
    specs: dict
    validated: bool
    export_control_check: bool

def validate_specs(state: MagnetState):
    required = ['flux_density', 'dimensions', 'coating']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid}

def check_export_regulations(state: MagnetState):
    # logic to review against dual-use criteria
    return {'export_control_check': True}

graph = StateGraph(MagnetState)
graph.add_node('validate', validate_specs)
graph.add_node('export_review', check_export_regulations)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
graph = graph.compile()