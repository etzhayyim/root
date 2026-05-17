from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OutdoorUmbrellaState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: OutdoorUmbrellaState):
    errors = []
    if state['specifications'].get('wind_resistance_mph', 0) < 20:
        errors.append('Wind resistance insufficient for public use')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def finalize_procurement(state: OutdoorUmbrellaState):
    print('Procurement validation complete.')
    return {}

builder = StateGraph(OutdoorUmbrellaState)
builder.add_node('validate', validate_specs)
builder.add_node('finalize', finalize_procurement)
builder.set_entry_point('validate')
builder.add_edge('validate', 'finalize')
builder.add_edge('finalize', END)
graph = builder.compile()