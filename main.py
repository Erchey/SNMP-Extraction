import asyncio
import time
from pysnmp.hlapi.v3arch.asyncio import *
from OIDs import *
from interfaces import get_interfaces

# Function to get SNMP data (for both inbound and outbound traffic)
async def get_snmp_data(snmpEngine, authData, transportTarget, oid):
    errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
        snmpEngine,
        authData,
        transportTarget,
        ContextData(),
        ObjectType(oid)
    )
    if errorIndication:
        print(f"Error: {errorIndication}")
        return None
    elif errorStatus:
        print(f"ErrorStatus: {errorStatus.prettyPrint()}")
        return None
    else:
        return varBinds[0][1]  # Return the value


# Function to calculate the difference between two octet values
def calculate_traffic_difference(previous_value, current_value):
    return current_value - previous_value


# Function to convert system uptime (timed ticks) to hours, minutes, and seconds
def convert_uptime(uptime_value):

    ticks = int(uptime_value)

    seconds = ticks // 100  # 100 ticks = 1 second
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return hours, minutes, seconds



# Main function to run the SNMP queries and update every 5 seconds
async def run():
    ifIndex = int(input('Enter interface: '))  # interface index
    inbound_oid = d_inbound_oid
    outbound_oid = d_outbound_oid
    uptime_oid = d_uptime_oid  # System uptime OID

    # OIDs for inbound and outbound octets using raw OIDs, appending the interface index
    in_octets_oid = ObjectIdentity(f'{inbound_oid}.{ifIndex}')
    out_octets_oid = ObjectIdentity(f'{outbound_oid}.{ifIndex}')
    uptime_octets_oid = ObjectIdentity(f'{uptime_oid}')

    authData = UsmUserData(
        'User2',
        authKey='Cisco1234',  
        authProtocol=usmHMACSHAAuthProtocol,  # SHA auth protocol
        privProtocol=usmNoPrivProtocol  # No privacy protocol
    )

    # SNMP engine
    snmpEngine = SnmpEngine()

    # Transport target for the SNMP request, with `create()` awaited
    transportTarget = await UdpTransportTarget.create(('192.168.100.5', 161))  # Port 161 is standard for SNMP

    # Initialize previous values for traffic calculation
    previous_in_octets = 0
    previous_out_octets = 0

    while True:
        # Get inbound traffic
        in_octets = await get_snmp_data(snmpEngine, authData, transportTarget, in_octets_oid)
        # Get outbound traffic
        out_octets = await get_snmp_data(snmpEngine, authData, transportTarget, out_octets_oid)
        # Get system uptime
        uptime_ticks = await get_snmp_data(snmpEngine, authData, transportTarget, uptime_octets_oid)

        # Handle inbound traffic
        if in_octets is not None:
            inbound_diff = calculate_traffic_difference(previous_in_octets, in_octets)
            previous_in_octets = in_octets
            print(f"Inbound Traffic (Octets): {inbound_diff} bytes")

        # Handle outbound traffic
        if out_octets is not None:
            outbound_diff = calculate_traffic_difference(previous_out_octets, out_octets)
            previous_out_octets = out_octets
            print(f"Outbound Traffic (Octets): {outbound_diff} bytes")

        # Handle uptime
        if uptime_ticks is not None:
            hours, minutes, seconds = convert_uptime(uptime_ticks)
            print(f"System Uptime: {hours} hours, {minutes} minutes, {seconds} seconds")

        # Wait for 5 seconds before refreshing data
        await asyncio.sleep(1)

asyncio.run(get_interfaces())
# Run the asyncio loop
asyncio.run(run())
