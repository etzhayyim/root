from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class MaterialState(TypedDict):
    material_code: str
    purity: float
    validation_passed: bool
    log: List[str]

def validate_material(state: MaterialState) -> MaterialState:
    # Specialized validation logic for high-purity metal alloys
    if state['purity'] >= 99.99:
        state['validation_passed'] = True
        state['log'].append('Material meets ultra-high purity standard.')
    else:
        state['validation_passed'] = False
        state['log'].append('Material failed purity threshold.')
    return state

def check_compliance(state: MaterialState) -> MaterialState:
    # Export control compliance check
    state['log'].append('Dual-use export control review completed.')
    return state

builder = StateGraph(MaterialState)
builder.add_node('validate', validate_material)
builder.add_node('compliance', check_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()