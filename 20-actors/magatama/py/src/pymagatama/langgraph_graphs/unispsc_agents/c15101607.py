from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ChemicalIngestState(TypedDict):
    material_id: str
    purity_level: float
    hazard_data: dict
    workflow_status: Annotated[Sequence[str], operator.add]

def validate_material(state: ChemicalIngestState) -> dict:
    # Logic to verify purity and safety standards
    status = 'Validated' if state['purity_level'] > 0.99 else 'Flagged'
    return {'workflow_status': [f'Material {state["material_id"]} {status}']}

def route_for_hazard(state: ChemicalIngestState) -> str:
    return 'process_hazardous' if state['hazard_data'].get('is_dangerous') else END

def process_hazardous(state: ChemicalIngestState) -> dict:
    return {'workflow_status': ['High-risk handling protocols activated']}

graph = StateGraph(ChemicalIngestState)
graph.add_node('validate', validate_material)
graph.add_node('process_hazardous', process_hazardous)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_for_hazard)
graph.add_edge('process_hazardous', END)

app = graph.compile()
