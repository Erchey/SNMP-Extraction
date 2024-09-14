import asyncio
import time
from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine, UsmUserData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, getCmd, usmHMACSHAAuthProtocol, usmNoPrivProtocol
)
from OIDs import *


async def run():
    
    ifIndex = 1  # interface index

    # OIDs for inbound and outbound octets using raw OIDs, appending the interface index
    in_octets_oid = ObjectIdentity(f'{inbound_oid}.{ifIndex}')
    out_octets_oid = ObjectIdentity(f'{outbound_oid}.{ifIndex}')
    uptime_octets_oid = ObjectIdentity(f'{uptime_oid}')

   
    authData = UsmUserData(
        'User2',
        authKey='Cisco1234',  # Replace with actual authentication key
        authProtocol=usmHMACSHAAuthProtocol,  # SHA auth protocol
        privProtocol=usmNoPrivProtocol  # No privacy protocol
    )

    # SNMP engine
    snmpEngine = SnmpEngine()

    # Transport target for the SNMP request, with `create()` awaited
    transportTarget = await UdpTransportTarget.create(('192.168.100.5', 161))  # Port 161 is standard for SNMP

    # Get inbound traffic
    errorIndication_in, errorStatus_in, errorIndex_in, varBinds_in = await getCmd(
        snmpEngine,
        authData,
        transportTarget,
        ContextData(),
        ObjectType(in_octets_oid)
    )

    # Get outbound traffic
    errorIndication_out, errorStatus_out, errorIndex_out, varBinds_out = await getCmd(
        snmpEngine,
        authData,
        transportTarget,
        ContextData(),
        ObjectType(out_octets_oid)
    )

     # Get system uptime
    errorIndication_uptime, errorStatus_uptime, errorIndex_uptime, varBinds_uptime = await getCmd(
        snmpEngine,
        authData,
        transportTarget,
        ContextData(),
        ObjectType(uptime_octets_oid)
    )


    # Handling inbound traffic response
    if errorIndication_in:
        print(f"Error (Inbound): {errorIndication_in}")
    elif errorStatus_in:
        print(f"ErrorStatus (Inbound): {errorStatus_in.prettyPrint()}")
    else:
        in_octets = varBinds_in[0][1]
        print(f"Inbound Traffic (Octets): {in_octets}")

    # Handling outbound traffic response
    if errorIndication_out:
        print(f"Error (Outbound): {errorIndication_out}")
    elif errorStatus_out:
        print(f"ErrorStatus (Outbound): {errorStatus_out.prettyPrint()}")
    else:
        out_octets = varBinds_out[0][1]
        print(f"Outbound Traffic (Octets): {out_octets}")

    # Handling system uptime response
    if errorIndication_uptime:
        print(f"Error (Uptime): {errorIndication_uptime}")
    elif errorStatus_uptime:
        print(f"ErrorStatus (Uptime): {errorStatus_uptime.prettyPrint()}")
    else:
        uptime = varBinds_uptime[0][1]
        print(f"System Uptime: {uptime}")


# Run the asyncio loop
asyncio.run(run())
