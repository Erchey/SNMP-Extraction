import asyncio
from pysnmp.hlapi.v3arch.asyncio import *
from OIDs import *
from interfaces import get_interfaces
from timeline import monitor_snmp_data


# Main function to run the asyncio loop
async def main():
    await get_interfaces()

    # Get interface index from user
    ifIndex = int(input('Enter interface: '))  # interface index

    # Start SNMP monitoring (data collection every 1 second) and database storage (e.g., every 5 minutes)
    await monitor_snmp_data(ifIndex, db_path='monitoring_data.db', store_interval=30)  # 300 seconds = 5 minutes

# Run the asyncio loop only once
try:
    asyncio.run(main())

except KeyboardInterrupt:
    print('Execution Interrupted')
