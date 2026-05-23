from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BedpanState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_material(state: BedpanState):
    material = state['specs'].get('material', '')
    compliant = material in ['Polypropylene', 'Stainless Steel']
    return {'is_compliant': compliant, 'validation_log': [f'Material {material} valid: {compliant}']}

def check_sanitation(state: BedpanState):
    is_autoclavable = state['specs'].get('autoclavable', False)
    return {'is_compliant': state['is_compliant'] and is_autoclavable, 'validation_log': state['validation_log'] + ['Sanitation check passed']}

graph = StateGraph(BedpanState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_sanitation', check_sanitation)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_sanitation')
graph.add_edge('check_sanitation', END)
graph = graph.compile()
