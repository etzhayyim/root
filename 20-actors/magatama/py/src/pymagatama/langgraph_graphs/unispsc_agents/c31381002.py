from typing import TypedDict
from langgraph.graph import StateGraph, END
class MagnetState(TypedDict):
    spec: dict
    validated: bool
    compliance_risk: str
def validate_specs(state: MagnetState):
    required = ['flux_density', 'dimensions']
    valid = all(k in state['spec'] for k in required)
    return {'validated': valid}
def check_export(state: MagnetState):
    if state.get('material_grade') == 'restricted':
        return {'compliance_risk': 'HIGH_EXPORT_CONTROL'}
    return {'compliance_risk': 'NONE'}
graph = StateGraph(MagnetState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_export)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
