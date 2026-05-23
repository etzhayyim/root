from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AluminumProcurementState(TypedDict):
    material_id: str
    purity: float
    composition: dict
    approved: bool
    validation_log: List[str]

def validate_material(state: AluminumProcurementState):
    log = []
    is_valid = True
    if state['purity'] < 99.7:
        log.append(f'Purity {state["purity"]} below 99.7% threshold.')
        is_valid = False
    return {'approved': is_valid, 'validation_log': log}

def prepare_shipping(state: AluminumProcurementState):
    return {'validation_log': state['validation_log'] + ['Logistics: Heat treatment verified.']}

def build_graph():
    workflow = StateGraph(AluminumProcurementState)
    workflow.add_node('validate', validate_material)
    workflow.add_node('shipping', prepare_shipping)
    workflow.set_entry_point('validate')
    workflow.add_edge('validate', 'shipping')
    workflow.add_edge('shipping', END)
    return workflow.compile()

graph = build_graph()
