from typing import TypedDict
from langgraph.graph import StateGraph, END

class IrradiationState(TypedDict):
    capsule_id: str
    radiation_data: dict
    compliance_checked: bool

def validate_capsule_specs(state: IrradiationState):
    # Business logic for capsule spec verification
    is_compliant = 'material' in state['radiation_data']
    return {'compliance_checked': is_compliant}

def export_control_check(state: IrradiationState):
    # Dual-use export control workflow
    print('Performing dual-use compliance scan...')
    return {'compliance_checked': True}

graph = StateGraph(IrradiationState)
graph.add_node('validate', validate_capsule_specs)
graph.add_node('export_check', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
app = graph.compile()
