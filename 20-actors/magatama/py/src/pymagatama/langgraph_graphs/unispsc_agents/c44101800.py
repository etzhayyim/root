from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CalcProcurementState(TypedDict):
    item_list: List[str]
    validation_errors: List[str]
    approved: bool

def validate_calculator_spec(state: CalcProcurementState):
    errors = []
    for item in state['item_list']:
        if 'power_source' not in item:
            errors.append(f'Missing power_source for {item}')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def finalize_order(state: CalcProcurementState):
    return {'approved': True}

graph = StateGraph(CalcProcurementState)
graph.add_node('validate', validate_calculator_spec)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()