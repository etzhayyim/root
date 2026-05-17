from typing import TypedDict
from langgraph.graph import StateGraph, END

class GasCutterState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: GasCutterState):
    required = ['gas_compatibility', 'safety_certification_iso']
    compliant = all(key in state['specs'] for key in required)
    return {'is_compliant': compliant, 'validation_log': ['Specs checked'] if compliant else ['Missing specs']}

def deploy_procurement(state: GasCutterState):
    return {'validation_log': state['validation_log'] + ['Procurement workflow initiated']}

graph = StateGraph(GasCutterState)
graph.add_node('validate', validate_specs)
graph.add_node('deploy', deploy_procurement)
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph.set_entry_point('validate')
graph = graph.compile()