import asyncio, datetime
from pysnmp.hlapi.v3arch.asyncio import *
from OIDs import *
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

# Function to convert uptime ticks into time format
def convert_ticks_to_time(ticks):
    seconds = ticks // 100  
    return str(datetime.timedelta(seconds=seconds))

# Function to monitor the SNMP data every 1 second
async def monitor_snmp_data(ifIndex, db_path, store_interval):
    inbound_oid = d_inbound_oid
    outbound_oid = d_outbound_oid
    uptime_oid = d_uptime_oid  # System uptime OID

    # OIDs for inbound and outbound octets, appending the interface index
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
    previous_in_octets = None
    previous_out_octets = None
    last_store_time = asyncio.get_event_loop().time()  # Track last time we stored data
    is_first_iteration = True  # Flag to skip first iteration for traffic calculation

    # Accumulators for cumulative traffic over the interval
    cumulative_inbound_traffic = 0
    cumulative_outbound_traffic = 0
    cumulative_total_traffic = 0

    while True:
        # Get inbound traffic
        in_octets = int(await get_snmp_data(snmpEngine, authData, transportTarget, in_octets_oid))
        # Get outbound traffic
        out_octets = int(await get_snmp_data(snmpEngine, authData, transportTarget, out_octets_oid))
        # Get system uptime
        uptime_ticks = int(await get_snmp_data(snmpEngine, authData, transportTarget, uptime_octets_oid))

        # Handle inbound traffic
        if in_octets is not None and previous_in_octets is not None and not is_first_iteration:
            inbound_diff = calculate_traffic_difference(previous_in_octets, in_octets)
            cumulative_inbound_traffic += inbound_diff  # Accumulate inbound traffic
            print(f"Inbound Traffic (Octets): {inbound_diff} bytes")
        previous_in_octets = in_octets  # Update previous inbound octets after every iteration

        # Handle outbound traffic
        if out_octets is not None and previous_out_octets is not None and not is_first_iteration:
            outbound_diff = calculate_traffic_difference(previous_out_octets, out_octets)
            cumulative_outbound_traffic += outbound_diff  # Accumulate outbound traffic
            print(f"Outbound Traffic (Octets): {outbound_diff} bytes")
        previous_out_octets = out_octets  # Update previous outbound octets after every iteration

        # Handle uptime
        if uptime_ticks is not None:
            hours, minutes, seconds = convert_uptime(uptime_ticks)
            print(f"System Uptime: {hours} hours, {minutes} minutes, {seconds} seconds")

        # Check if it's time to store data in the database
        current_time = asyncio.get_event_loop().time()
        if current_time - last_store_time >= store_interval:
            # Calculate total traffic for the interval
            cumulative_total_traffic = cumulative_inbound_traffic + cumulative_outbound_traffic  

            # Convert uptime to time format
            uptime_ticks_int = convert_ticks_to_time(int(uptime_ticks))  # Cast uptime to time

            # **Store data in DB even if traffic is zero**
            store_data_in_db(db_path, cumulative_total_traffic, uptime_ticks_int, cumulative_inbound_traffic, cumulative_outbound_traffic)
            print(f"Data stored in DB at time: {hours}h {minutes}m {seconds}s")

            # Reset the cumulative traffic counters after storing
            cumulative_inbound_traffic = 0
            cumulative_outbound_traffic = 0

            last_store_time = current_time  # Update last store time

        # Skip the first result for traffic calculation
        is_first_iteration = False

        # Refresh every 1 second for data collection
        await asyncio.sleep(1)
