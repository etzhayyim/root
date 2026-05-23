from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CarbonMaterialState(TypedDict):
    material_id: str
    purity_level: float
    validation_log: Annotated[Sequence[str], operator.add]
    status: str

def validate_carbon_specs(state: CarbonMaterialState):
    if state['purity_level'] < 99.99:
        return {'status': 'REJECTED', 'validation_log': ['Low purity detected']}
    return {'status': 'VALIDATED', 'validation_log': ['Purity check passed']}

def process_procurement(state: CarbonMaterialState):
    return {'validation_log': ['Proceeding to supply chain routing']}

builder = StateGraph(CarbonMaterialState)
builder.add_node('validate', validate_carbon_specs)
builder.add_node('process', process_procurement)
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
builder.set_entry_point('validate')
graph = builder.compile()
