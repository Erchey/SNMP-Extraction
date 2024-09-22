import asyncio, time
from pysnmp.hlapi.v3arch.asyncio import *
from OIDs import *
from interfaces import get_interfaces
from database import store_data_in_db

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

# Function to monitor the SNMP data every 1 second
async def monitor_snmp_data(ifIndex, db_path, store_interval):
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

    # Transport target for the SNMP request
    transportTarget = await UdpTransportTarget.create(('192.168.100.5', 161))  # Port 161 is standard for SNMP

    # Initialize previous values for traffic calculation
    previous_in_octets = 0
    previous_out_octets = 0
    last_store_time = asyncio.get_event_loop().time()  # Track last time we stored data

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

        # Check if it's time to store data in the database
        current_time = asyncio.get_event_loop().time()
        if current_time - last_store_time >= store_interval:
            if in_octets is not None and out_octets is not None and uptime_ticks is not None:
                inbound_traffic = int(in_octets)
                outbound_traffic = int(out_octets)
                total_traffic = inbound_traffic + outbound_traffic  
                uptime_ticks_int = int(uptime_ticks)  # Cast uptime to int
                store_data_in_db(db_path, total_traffic, uptime_ticks_int, inbound_traffic, outbound_traffic)  # Pass int values to the database
                print(f"Data stored in DB at time: {hours}h {minutes}m {seconds}s")

            last_store_time = current_time  # Update last store time

        # Refresh every 1 second for data collection
        await asyncio.sleep(1)

def collect_data():
    """Simulate data collection; replace with actual logic."""
    return 100  # Example data value, replace with actual data gathering logic

def get_system_uptime():
    """Simulate system uptime collection; replace with actual logic to query uptime."""
    return time.time()  # Replace this with actual uptime query (e.g., from SNMP)