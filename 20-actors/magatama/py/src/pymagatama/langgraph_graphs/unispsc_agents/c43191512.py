from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class GraphState(TypedDict):
    task_id: str
    gpu_spec: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_gpu_spec(state: GraphState):
    spec = state['gpu_spec']
    results = []
    if spec.get('thermal_design_power_w', 0) > 450:
        results.append('TDP exceeds standard cooling capacity')
    return {'validation_results': results}

def check_compliance(state: GraphState):
    is_compliant = len(state['validation_results']) == 0
    return {'is_compliant': is_compliant}

graph = StateGraph(GraphState)
graph.add_node('validate', validate_gpu_spec)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
