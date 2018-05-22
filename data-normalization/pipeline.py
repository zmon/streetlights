#!/usr/bin/env python3
"""
This is an etl pipeline and 
is not intended to be used as part of the 
webapplication. The purpose of a pipeline
is to have uniform data format we can use
for bulk loading the db. If we get random flat
files we can feed them through a pipeline.

author: Chris Whitehead
github: cgwhitehead

TODO:
    *Identify any function that could be reused for multiple piplines
    **move to a central pipline function area
    *Work with SMEs to see if we are understanding light posts correctly. 
"""
import petl as etl


def geom_to_tuple(geom: str) -> tuple:
    """
    Args:
        geom: combined KCMO style point string ie. POINT (-94.574238674757 39.021251335024)
    Returns:
        latitude and longitude as floats
    """
    lat, long = geom.replace('POINT', '').strip('( )').split(' ')
    return float(lat), float(long)


def remove_empty(items: list) -> list:
    """Takes a list of items and returns elements that are not empty"""
    return [x for x in items if x is not None]


def find_wifi(*args) -> bool:
    """
    Args:
        args: Any number of fields
    Returns:
        Whether the fields indicate wifi
    """
    wifilist = ['Google', 'Sprint', 'Wireless', 'Mobil']
    for x in args:
        if x is not None:
            if any(word in x for word in wifilist):
                return True
    return False


def kcmo_convert(filepath: str, xtrapath: str):
    """
    Takes the both KCMO input datasets and
    converts to universal format under data/kcmo_clean.csv

    Args:
        filepath: Path to primary kcmo csv dataset
        xtrapath: Path to additional kcmo xlsx dataset
    """
    kcmo = etl.fromcsv(filepath)
    kcx = etl.fromxlsx(xtrapath)
    kcjoin = etl.join(kcmo, kcx, lkey='POLEID', rkey='IDNumber')
    del kcmo
    del kcx

    kcjoin = etl.addfield(kcjoin, 'PoleID', lambda x: x['POLEID'])
    kcjoin = etl.addfield(kcjoin, 'Longitude', lambda x: geom_to_tuple(x['the_geom'])[0])
    kcjoin = etl.addfield(kcjoin, 'Latitude', lambda x: geom_to_tuple(x['the_geom'])[1])
    kcjoin = etl.addfield(kcjoin, 'LightbulbType', lambda x: x['LUMINAIRE TYPE'])
    kcjoin = etl.addfield(kcjoin, 'Wattage', lambda x: x['WATTS'])
    kcjoin = etl.addfield(kcjoin, 'Lumens', None)
    kcjoin = etl.addfield(kcjoin, 'LightAttributes', lambda x: remove_empty([
        x['ATTACHMENT 10'], x['ATTACHMENT 9'], x['ATTACHMENT 8'],
        x['ATTACHMENT 7'], x['ATTACHMENT 6'], x['ATTACHMENT 5'],
        x['ATTACHMENT 4'], x['ATTACHMENT 3'], x['ATTACHMENT 2'],
        x['ATTACHMENT 1'], x['SPECIAL_N2'], x['SPECIAL_NO']
    ]))
    kcjoin = etl.addfield(kcjoin, 'AttachedTech', lambda x: bool(x['LightAttributes']))
    kcjoin = etl.addfield(kcjoin, 'FiberWiFiEnable', lambda x: find_wifi(
        *x['LightAttributes'], x['SPECIAL_N2'], x['SPECIAL_NO']
    ))
    kcjoin = etl.addfield(kcjoin, 'PoleType', lambda x: x['POLE TYPE'])
    kcjoin = etl.addfield(kcjoin, 'PoleOwner', lambda x: x['POLE OWNER'])
    kcjoin = etl.addfield(kcjoin, 'DataSource', 'Kansas City')
    kcjoin = etl.cut(kcjoin, 'PoleID', 'Longitude', 'Latitude', 'LightbulbType',
                     'Wattage', 'Lumens', 'AttachedTech', 'LightAttributes',
                     'FiberWiFiEnable', 'PoleType', 'PoleOwner', 'DataSource')
    etl.tocsv(kcjoin, 'data/kcmo_clean.csv')


def lee_convert(filepath: str):
    """
    Converts lee summit's csv into a universal csv
    under data/kcleesummit_clean.csv

    Args:
        filepath: Path to lee summit csv
    """
    kclee = etl.fromcsv(filepath)

    kclee = etl.addfield(kclee, 'PoleID', lambda x: 'KCLEE' + x['OBJECTID'])
    kclee = etl.addfield(kclee, 'Longitude', lambda x: x['POINT_X'])
    kclee = etl.addfield(kclee, 'Latitude', lambda x: x['POINT_Y'])
    kclee = etl.addfield(kclee, 'LightbulbType', lambda x: x['LAMPTYPE'])
    kclee = etl.addfield(kclee, 'Wattage', lambda x: x['WATTS'])
    kclee = etl.addfield(kclee, 'Lumens', lambda x: x['LUMENS'])
    kclee = etl.addfield(kclee, 'AttachedTech', False)
    kclee = etl.addfield(kclee, 'LightAttributes', lambda x: x['FIXTURETYP'])
    kclee = etl.addfield(kclee, 'FiberWiFiEnable', False)
    kclee = etl.addfield(kclee, 'PoleType', None)
    kclee = etl.addfield(kclee, 'PoleOwner', 'Lee Summit')
    kclee = etl.addfield(kclee, 'DataSource', 'Lee Summit')
    kclee = etl.cut(kclee, 'PoleID', 'Longitude', 'Latitude', 'LightbulbType',
                    'Wattage', 'Lumens', 'AttachedTech', 'LightAttributes',
                    'FiberWiFiEnable', 'PoleType', 'PoleOwner', 'DataSource')
    etl.tocsv(kclee, 'data/kcleesummit_clean.csv')


def main():
    # for testing
    filepath = 'data/kansas-city-mo.csv'
    xtrapath = 'data/kansas-city-mo-extra.xlsx'
    filepath_lee = 'data/lee-summit-mo.csv'
    kcmo_convert(filepath, xtrapath)
    lee_convert(filepath_lee)
    print('done')


if __name__ == '__main__':
    main()
