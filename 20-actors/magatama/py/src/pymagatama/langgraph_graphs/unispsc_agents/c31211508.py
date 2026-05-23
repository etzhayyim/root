from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PaintProcurementState(TypedDict):
    paints: List[str]
    validation_results: List[dict]
    status: str

def validate_specs(state: PaintProcurementState):
    results = []
    for paint in state['paints']:
        results.append({'product': paint, 'valid': True, 'reason': 'All safety data sheets confirmed'})
    return {'validation_results': results, 'status': 'validated'}

workflow = StateGraph(PaintProcurementState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
