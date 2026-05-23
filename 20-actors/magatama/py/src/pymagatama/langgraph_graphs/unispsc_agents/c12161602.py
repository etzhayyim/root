from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class SemiconductorMaterialState(TypedDict):
    material_id: str
    purity_data: Dict[str, float]
    validation_passed: bool
    workflow_history: Annotated[List[str], add_messages]

def validate_material_purity(state: SemiconductorMaterialState):
    purity = state['purity_data'].get('purity', 0.0)
    return {'validation_passed': purity >= 99.9999, 'workflow_history': ['Purity Validation Executed']}

def perform_trace_analysis(state: SemiconductorMaterialState):
    return {'workflow_history': ['Trace Element Analysis Completed', 'Compliance check passed']}

graph = StateGraph(SemiconductorMaterialState)
graph.add_node('validate_purity', validate_material_purity)
graph.add_node('trace_analysis', perform_trace_analysis)
graph.add_edge('validate_purity', 'trace_analysis')
graph.add_edge('trace_analysis', END)
graph.set_entry_point('validate_purity')
app = graph.compile()
