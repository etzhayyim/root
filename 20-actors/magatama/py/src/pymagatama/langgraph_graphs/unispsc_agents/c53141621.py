from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    specs: dict
    validated: bool
    compliance_report: str

def validate_threader_specs(state: ProcurementState):
    required_keys = ['wire_gauge', 'material_type']
    valid = all(k in state['specs'] for k in required_keys)
    return {'validated': valid, 'compliance_report': 'Validated' if valid else 'Missing specs'}

def finalize_procurement(state: ProcurementState):
    return {'compliance_report': f'Procurement approved for {state[item_name]}'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_threader_specs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()