from pysnmp.hlapi.v3arch.asyncio import *
from OIDs import d_if_descr


async def get_interfaces():
    # SNMP User Auth (Update 'User2' and 'Cisco1234' to your actual credentials)
    authData = UsmUserData(
        'User2',
        authKey='Cisco1234',
        authProtocol=usmHMACSHAAuthProtocol,  # SHA auth protocol
        privProtocol=usmNoPrivProtocol  # No privacy protocol
    )

    # SNMP Engine setup
    snmpEngine = SnmpEngine()

    # Transport target for the SNMP request
    transportTarget = await UdpTransportTarget.create(('192.168.100.5', 161))  # Replace with actual device IP

    # OID for the ifDescr table (interface descriptions) base
    base_oid = d_if_descr

    print("Querying interface descriptions dynamically...")

    # Initialize index to start from
    i = 1
    interface_count = 0  # Counter for the number of interfaces found

    # Loop until the result is None (indicating no more interfaces)
    while True:
        oid = ObjectIdentity(f'{base_oid}.{i}')  # Query for ifDescr.i
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            snmpEngine,
            authData,
            transportTarget,
            ContextData(),
            ObjectType(oid)
        )

        # Handle errors
        if errorIndication:
            print(f"Error: {errorIndication}")
            break
        elif errorStatus:
            print(f"ErrorStatus: {errorStatus.prettyPrint()}")
            break
        else:
            for varBind in varBinds:
                if not varBind[1]:  # Check if the result is empty (None or Null)
                    print(f"\nTotal number of interfaces found: {interface_count}\n")
                    return
                print(f"{varBind[0]} = {varBind[1]}")
                interface_count += 1  # Increment the interface count

        # Increment the index for the next interface
        i += 1

