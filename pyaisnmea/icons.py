"""
all the different icons we have to represent different types of AIS stations

ICONS(dict): keys are the AIS station type as a string, values are the filename
             of the icon
"""

ICONS = {'Base Station': 'basestn.png',
         'Class A': 'classa.png',
         'Navigation Aid': 'navaid.png',
         'Class B': 'classb.png',
         'Unknown': 'unknown.png',
         'SAR Aircraft': 'sar.png',
         'Law Enforcement': 'lawenforcement.png',
         'Tug': 'tug.png',
         'Pilot Vessel': 'pilot.png',
         'Towing': 'towing.png',
         ('Towing: length exceeds 200m or breadth exceeds'
          ' 25m'): 'towinglarge.png',
         'Sailing': 'sailing.png',
         'Search and Rescue vessel': 'shipsar.png',
         ('Noncombatant ship according to '
          'RR Resolution No. 18'): 'medicaltransport.png',
         'Medical Transport': 'medicaltransport.png',
         'Dredging or underwater ops': 'dredger.png',
         'Military ops': 'military.png',
         'Port Tender': 'porttender.png',
         'Passenger, all ships of this type': 'passenger.png',
         'Passenger, Hazardous category A': 'passengerhaza.png',
         'Passenger, Hazardous category B': 'passengerhazb.png',
         'Passenger, Hazardous category C': 'passengerhazc.png',
         'Passenger, Hazardous category D': 'passengerhazd.png',
         'Passenger, Reserved for future use': 'passenger.png',
         'Passenger, No additional information': 'passenger.png',
         'Cargo, all ships of this type': 'cargo.png',
         'Cargo, Reserved for future use': 'cargo.png',
         'Cargo, No additional information': 'cargo.png',
         'Cargo, Hazardous category A': 'cargohaza.png',
         'Cargo, Hazardous category B': 'cargohazb.png',
         'Cargo, Hazardous category C': 'cargohazc.png',
         'Cargo, Hazardous category D': 'cargohazd.png',
         'Tanker, all ships of this type': 'tanker.png',
         'Tanker, Reserved for future use': 'tanker.png',
         'Tanker, No additional information': 'tanker.png',
         'Tanker, Hazardous category A': 'tankerhaza.png',
         'Tanker, Hazardous category B': 'tankerhazb.png',
         'Tanker, Hazardous category C': 'tankerhazc.png',
         'Tanker, Hazardous category D': 'tankerhazd.png',
         'Not available (default)': 'ship.png',
         'Other Type, all ships of this type': 'ship.png',
         'Other Type, Reserved for future use': 'ship.png',
         'Other Type, no additional information': 'ship.png',
         'Other Type, Hazardous category A': 'shiphaza.png',
         'Other Type, Hazardous category B': 'shiphazb.png',
         'Other Type, Hazardous category C': 'shiphazc.png',
         'Other Type, Hazardous category D': 'shiphazd.png',
         'Reserved for future use': 'reserved.png',
         'Reserved': 'reserved.png',
         'Spare, Reserved for future use.': 'reserved.png',
         'Special Mark': 'specialmark.png',
         'Safe Water': 'safewater.png',
         'Isolated danger': 'isolateddanger.png',
         'Cardinal Mark W': 'cardinalmarkw.png',
         'Cardinal Mark E': 'cardinalmarke.png',
         'Cardinal Mark N': 'cardinalmarkn.png',
         'Cardinal Mark S': 'cardinalmarks.png',
         'RACON (radar transponder marking a navigation hazard)': 'racon.png',
         ('Fixed structure off shore, such as oil platforms, '
          'wind farms,'): 'fixedstructure.png',
         'Default Nav Aid, not specified': 'navaid.png',
         'Beacon, Cardinal N': 'cardinalmarkn.png',
         'Beacon, Cardinal E': 'cardinalmarke.png',
         'Beacon, Cardinal S': 'cardinalmarks.png',
         'Beacon, Cardinal W': 'cardinalmarkw.png',
         'Beacon, Isolated danger': 'isolateddanger.png',
         'Beacon, Safe water': 'safewater.png',
         'Beacon, Special mark': 'specialmark.png',
         'Spare - Local Vessel': 'ship.png',
         'Wing in ground (WIG), all ships of this type': 'winginground.png',
         'Wing in ground (WIG), Reserved for future use': 'winginground.png',
         'Wing in ground (WIG), Hazardous category A': 'wingingroundhaza.png',
         'Wing in ground (WIG), Hazardous category B': 'wingingroundhazb.png',
         'Wing in ground (WIG), Hazardous category C': 'wingingroundhazc.png',
         'Wing in ground (WIG), Hazardous category D': 'wingingroundhazd.png',
         ('High speed craft (HSC), all ships of this '
          'type'): 'highspeedcraft.png',
         ('High speed craft (HSC), Reserved for future '
          'use'): 'highspeedcraft.png',
         ('High speed craft (HSC), No additional '
          'information'): 'highspeedcraft.png',
         ('High speed craft (HSC), Hazardous category '
          'A'): 'highspeedcrafthaza.png',
         ('High speed craft (HSC), Hazardous category '
          'B'): 'highspeedcrafthazb.png',
         ('High speed craft (HSC), Hazardous category '
          'C'): 'highspeedcrafthazc.png',
         ('High speed craft (HSC), Hazardous category '
          'D'): 'highspeedcrafthazd.png',
         'Diving ops': 'diving.png',
         'Fishing': 'fishing.png',
         'Pleasure Craft': 'pleasurecraft.png',
         'Anti-pollution equipment': 'antipollution.png',
         'Light Vessel / LANBY / Rigs': 'lightship.png',
         'Light, without sectors': 'lighthouse.png',
         'Light, with sectors': 'lighthousewithsectors.png',
         'Leading Light Front': 'leadinglightfront.png',
         'Leading Light Rear': 'leadinglightrear.png',
         'Auxiliary craft associated with a parent ship': 'auxiliary.png',
         'MOB (Man Overboard) device': 'mob.png',
         'AIS SART (Search and Rescue Transmitter)': 'aissart.png',
         'EPIRB (Emergency Position Indicating Radio Beacon)': 'epirb.png',
         'Portable VHF Transceiver': 'portablevhf.png',
         'Reference point': 'referencepoint.png'}


REGIONA = {
    'Preferred Channel Port hand': 'preferredchannelport.png',
    'Port hand Mark': 'port.png',
    'Beacon, Port hand': 'port.png',
    'Beacon, Preferred Channel port hand': 'port.png',
    'Preferred Channel Starboard hand': 'preferredchannelstarboard.png',
    'Starboard hand Mark': 'starboard.png',
    'Beacon, Starboard hand': 'starboard.png',
    'Beacon, Preferred Channel starboard hand': 'starboard.png'}


REGIONB = {
    'Preferred Channel Port hand': 'preferredchannelportB.png',
    'Port hand Mark': 'portB.png',
    'Beacon, Port hand': 'portB.png',
    'Beacon, Preferred Channel port hand': 'portB.png',
    'Preferred Channel Starboard hand': 'preferredchannelstarboardB.png',
    'Starboard hand Mark': 'starboardB.png',
    'Beacon, Starboard hand': 'starboardB.png',
    'Beacon, Preferred Channel starboard hand': 'starboardB.png'}


def switch_IALA_region(region):
    """
    switch between IALA region A and B

    Note:
        Region A = Rest of the world
        Region B = North and South America (excluding Greenland),
                   Japan, Korea and the Philippines

    Args:
        region(str): IALA region either A or B
    """
    if region in ('A', 'a'):
        ICONS.update(REGIONA)
    elif region in ('B', 'b'):
        ICONS.update(REGIONB)


def all_icons():
    """
    return a set of all icons available

    Returns:
        allicons(set): set of all icon filenames including
                       ones for both regions
    """
    allicons = set(ICONS.values())
    allicons.update(REGIONA.values())
    allicons.update(REGIONB.values())
    return allicons
