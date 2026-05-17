from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CoalProcurementState(TypedDict):
    carbon_content: float
    moisture: float
    status: str
    validation_log: Annotated[Sequence[str], operator.add]

def validate_coal_quality(state: CoalProcurementState):
    log = []
    if state['carbon_content'] < 80.0:
        log.append(f'Carbon content {state['carbon_content']}% below threshold')
    if state['moisture'] > 12.0:
        log.append(f'Moisture level {state['moisture']}% exceeds limit')
    
    new_status = 'REJECTED' if log else 'APPROVED'
    return {'status': new_status, 'validation_log': log}

def update_inventory(state: CoalProcurementState):
    return {'status': f'{state['status']}_INVENTORY_UPDATED'}

builder = StateGraph(CoalProcurementState)
builder.add_node('validate', validate_coal_quality)
builder.add_node('inventory', update_inventory)
builder.add_edge('validate', 'inventory')
builder.set_entry_point('validate')
builder.add_edge('inventory', END)
graph = builder.compile()