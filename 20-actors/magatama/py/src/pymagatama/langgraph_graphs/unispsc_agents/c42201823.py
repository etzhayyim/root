from typing import TypedDict
from langgraph.graph import StateGraph, END

class XrayProcurementState(TypedDict):
    voltage_rating: float
    safety_certs: list
    compliance_validated: bool

def validate_safety(state: XrayProcurementState):
    required = ['IEC60601', 'FDA_510K']
    valid = all(cert in state['safety_certs'] for cert in required)
    return {'compliance_validated': valid}

def check_voltage(state: XrayProcurementState):
    if state['voltage_rating'] > 150:
        print('High voltage alert: Export license review required.')
    return {}

builder = StateGraph(XrayProcurementState)
builder.add_node('validate_safety', validate_safety)
builder.add_node('check_voltage', check_voltage)
builder.set_entry_point('validate_safety')
builder.add_edge('validate_safety', 'check_voltage')
builder.add_edge('check_voltage', END)
graph = builder.compile()
