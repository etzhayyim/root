from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    chemical_data: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_chemical_safety(state: ChemicalProcurementState):
    # Simulate MSDS and safety validation
    logs = [f"Validating CAS: {state['chemical_data'].get('cas')}"]
    return {'validation_logs': logs, 'is_compliant': True}

def prepare_logistics(state: ChemicalProcurementState):
    logs = ["Arranging dangerous goods transport protocols"]
    return {'validation_logs': logs}

graph = StateGraph(ChemicalProcurementState)
graph.add_node("safety_check", validate_chemical_safety)
graph.add_node("logistics_prep", prepare_logistics)
graph.add_edge("safety_check", "logistics_prep")
graph.add_edge("logistics_prep", END)
graph.set_entry_point("safety_check")
compiled_graph = graph.compile()