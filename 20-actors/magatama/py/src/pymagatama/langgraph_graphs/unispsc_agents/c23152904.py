from typing import TypedDict
from langgraph.graph import StateGraph, END

class LaserState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: str

def validate_laser_specs(state: LaserState):
    specs = state['spec_data']
    power = specs.get('output_power_watts', 0)
    compliant = power > 0 and 'safety_interlock_certification' in specs
    return {'is_compliant': compliant, 'validation_log': 'Validated' if compliant else 'Missing specs'}

workflow = StateGraph(LaserState)
workflow.add_node('validation', validate_laser_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()