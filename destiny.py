import Manifest
import json

DESTINY_URL = 'https://www.bungie.net/Platform/Destiny2/'


'''
Helpful Enumerations
'''

COMPONENTS = {
    'None': '0',
    'Profiles': '100',
    'VendorReceipts': '101',
    'ProfileInventories': '102',
    'ProfileCurrencies': '103',
    'ProfileProgression': '104',
    'Characters': '200',
    'CharacterInventories': '201',
    'CharacterProgressions': '202',
    'CharacterRenderData': '203',
    'CharacterActivities': '204',
    'CharacterEquipment': '205',
    'ItemInstances': '300',
    'ItemObjectives': '301',
    'ItemPerks': '302',
    'ItemRenderData': '303',
    'ItemStats': '304',
    'ItemSockets': '305',
    'ItemTalentGrids': '306',
    'ItemCommonData': '307',
    'ItemPlugStates': '308',
    'Vendors': '400',
    'VendorCategories': '401',
    'VendorSales': '402',
    'Kiosks': '500',
    'CurrencyLookups': '600',
    'PresentationNodes': '700',
    'Collectibles': '800',
    'Records': '900'

}

EQUIP_FAILURE_REASON = {
    'None': 0,
    'ItemUnequippable': 1,
    'ItemUniqueEquipRestricted': 2,
    'ItemFailedUnlockCheck': 4,
    'ItemFailedLevelCheck': 8,
    'ItemNotOnCharacter': 16
}

BUCKET_TYPE = {
    #'Consumables': 1469714392,
    'Kinetic Weapons': 1498876634,
    'Energy Weapons': 2465295065,
    'Power Weapons': 953998645,
    'Helmet': 3448274439,
    'Gauntlets': 3551918588,
    'Chest Armor': 14239492,
    'Leg Armor': 20886954,
    'Class Armor': 1585787867,
    #'Ghost': 4023194814,
    #'Vehicle': 2025709351,
    #'Ships': 284967655,
    #'Subclass': 3284755031
}

ITEM_LOCATION = {
    'Unknown': 0,
    'Inventory': 1,
    'Vault': 2,
    'Vendor': 3,
    'Postmaster': 4
}

TRANSFER_STATUS = {
    0: "CanTransfer: The item can be transferred.",
    1: "ItemIsEquipped: You can't transfer the item because it is equipped on a character.",
    2: "NotTransferable: The item is defined as not transferable in its DestinyInventoryItemDefinition.nonTransferable property.",
    4: "NoRoomInDestination: You could transfer the item, but the destination is full"
}

ARMOR_TYPES = [
    'HelmetArmor',
    'ArmsArmor',
    'ChestArmor',
    'LegArmor',
    'ClassArmor']


'''
Core Functions

These functions provide interaction with the endpoints required to perform tasks associated with the app.
they are named for and map to the functions outlined in the official docs at https://bungie-net.github.io
'''


def getProfile(session,membershiptype,membershipid,components):
    req_str = DESTINY_URL + '{}/Profile/{}?components={}'.format(membershiptype,membershipid,components)
    response = session.get(req_str)
    profile = json.loads(response.content)
    if profile['ErrorCode'] != 1:
        raise APIError(profile['Message'])
    result = profile['Response']
    return result


def getCharacter(session,membershiptype,membershipid,characterid, components):
    req_str = DESTINY_URL + '{}/Profile/{}/Character/{}'.format(membershiptype,membershipid,characterid) \
              +'?components={}'.format(components)
    response = session.get(req_str)
    character = json.loads(response.content)
    if character['ErrorCode'] != 1:
        raise APIError(character['Message'])
    result = character['Response']
    return result


def getItem(session, membershiptype, membershipid, iteminstanceid, components):
    req_str = DESTINY_URL + '{}/Profile/{}/Item/{}/'.format(membershiptype,membershipid,iteminstanceid) \
              + '?components={}'.format(components)
    response = session.get(req_str)
    item = json.loads(response.content)
    if item['ErrorCode'] != 1:
        raise APIError(item['Message'])
    result = item['Response']
    return result


def transferItem(session, membershiptype, characterid, itemreference, itemid, stacksize, toVault):
    req_str = DESTINY_URL + 'Actions/Items/TransferItem/'
    payload = {
        "itemReferenceHash": itemreference,
        "stackSize": stacksize,
        "transferToVault": toVault,
        "itemId": itemid,
        "characterId": characterid,
        "membershipType": membershiptype
    }
    post_data = json.dumps(payload)
    response = session.post(req_str, data=post_data)
    res = json.loads(response.content)
    if res['ErrorCode'] != 1:
        raise TransferError(response['Message'])
    return


def equipItem(session, itemid, characterid, membershiptype):
    req_str = DESTINY_URL + 'Actions/Items/EquipItem/'
    payload = {
        "itemId": itemid,
        "characterId": characterid,
        "membershipType": membershiptype
    }
    post_data = json.dumps(payload)
    response = session.post(req_str, data=post_data)
    res = json.loads(response.content)
    if res['ErrorCode'] != 1:
        raise EquipError(response['Message'])
    return


def equipItems(session, itemids, characterid, membershiptype):
    req_str = DESTINY_URL + 'Actions/Items/EquipItem/'
    payload = {
        "itemId": itemids,
        "characterId": characterid,
        "membershipType": membershiptype
    }
    post_data = json.dumps(payload)
    response = session.post(req_str, data=post_data)
    res = json.loads(response.content)
    if res['ErrorCode'] != 1:
        raise EquipError(response['Message'])
    return response


'''
Helping Functions

These functions provide further assistance in implementing the core functionality provided by the Destiny API
'''


#TODO: This is the call that fails to authenticate
    # See Auth is partially broken in Prod
    # Without Read non equipped inventory CharacterInventories and ProfileInventories are empty
def buildInventory(session, membershiptype, membershipid):
    response = getProfile(session, membershiptype, membershipid, COMPONENTS['ProfileInventories'] + ',' +
                          COMPONENTS['CharacterInventories'] + ',' + COMPONENTS['CharacterEquipment'] + ',' +
                          COMPONENTS['ItemInstances'] + ',' + COMPONENTS['ItemSockets'])
    items = response['profileInventory']['data']['items']
    inventory = Inventory(membershipid)

    # Add char inventory and equipment to all items list
    for char in response['characterInventories']['data']:
        charinv = response['characterInventories']['data'][char]['items']
        for item in charinv:
            items.append(item)
        chareq = response['characterEquipment']['data'][char]['items']
        for item in chareq:
            items.append(item)
    # begin item instantiation
    for item in items:
        if "itemInstanceId" in item: # eliminate non instanced items
            a = Item(item['itemHash'],item['itemInstanceId'])
            if a.inventory['bucketTypeHash'] not in BUCKET_TYPE.values(): # items that aren't included in Loadouts
                continue
            if "primaryStat" in response['itemComponents']['instances']['data'][a.itemInstanceId]:
                a.stats['primaryStat'] = response['itemComponents']['instances']['data'][a.itemInstanceId]['primaryStat']
            else:
                a.stats['primaryStat'] = 0
            itemSocketSet = {}
            itemSocketSet["sockets"] = []
            if a.itemInstanceId in response["itemComponents"]["sockets"]["data"]:
                for socket in response["itemComponents"]["sockets"]["data"][a.itemInstanceId]["sockets"]:
                    if 'reusablePlugHashes' in socket:
                        if socket["reusablePlugHashes"].__len__() > 0:
                            column = []
                            for plug in socket["reusablePlugHashes"]:
                                column.append(Socket(plug))
                            set = SocketSet(Socket(socket['plugHash']), column)
                            itemSocketSet["sockets"].append(set)
                a.sockets = itemSocketSet["sockets"]
            if a.inventory['bucketTypeHash'] == BUCKET_TYPE['Kinetic Weapons']:
                inventory.kinetic.append(a)
            if a.inventory['bucketTypeHash'] == BUCKET_TYPE['Energy Weapons']:
                inventory.energy.append(a)
            if a.inventory['bucketTypeHash'] == BUCKET_TYPE['Power Weapons']:
                inventory.power.append(a)
            if a.inventory['bucketTypeHash'] == BUCKET_TYPE['Helmet']:
                if 21 in a.categories:
                    inventory.warlockArmor["HelmetArmor"].append(a)
                if 22 in a.categories:
                    inventory.titanArmor["HelmetArmor"].append(a)
                if 23 in a.categories:
                    inventory.hunterArmor["HelmetArmor"].append(a)
            if a.inventory['bucketTypeHash'] == BUCKET_TYPE['Gauntlets']:
                if 21 in a.categories:
                    inventory.warlockArmor["ArmsArmor"].append(a)
                if 22 in a.categories:
                    inventory.titanArmor["ArmsArmor"].append(a)
                if 23 in a.categories:
                    inventory.hunterArmor["ArmsArmor"].append(a)
            if a.inventory['bucketTypeHash'] == BUCKET_TYPE['Chest Armor']:
                if 21 in a.categories:
                    inventory.warlockArmor["ChestArmor"].append(a)
                if 22 in a.categories:
                    inventory.titanArmor["ChestArmor"].append(a)
                if 23 in a.categories:
                    inventory.hunterArmor["ChestArmor"].append(a)
            if a.inventory['bucketTypeHash'] == BUCKET_TYPE['Leg Armor']:
                if 21 in a.categories:
                    inventory.warlockArmor["LegArmor"].append(a)
                if 22 in a.categories:
                    inventory.titanArmor["LegArmor"].append(a)
                if 23 in a.categories:
                    inventory.hunterArmor["LegArmor"].append(a)
            if a.inventory['bucketTypeHash'] == BUCKET_TYPE['Class Armor']:
                if 21 in a.categories:
                    inventory.warlockArmor["ClassArmor"].append(a)
                if 22 in a.categories:
                    inventory.titanArmor["ClassArmor"].append(a)
                if 23 in a.categories:
                    inventory.hunterArmor["ClassArmor"].append(a)
    return inventory


#TODO: Was this written for exactly the purpose of adding API info to Items on load?
    # No it was the one-by-one item build that takes forever but it may be useful
    # This function in unused in submission copy.
def setItemProperties(session, membershiptype, membershipid, item):
    result = getItem(session, membershiptype, membershipid, item.itemInstanceId, COMPONENTS['ItemInstances'] + ',' +
                     COMPONENTS['ItemSockets'])
    item.stats['primaryStat'] = result['instance']['data']['primaryStat']
    itemSocketSet = {}
    itemSocketSet["sockets"] = []
    for socket in result["sockets"]["data"]["sockets"]:
        if 'reusablePlugHashes' in socket:
            if socket["reusablePlugHashes"].__len__() > 0:
                column = []
                for plug in socket["reusablePlugHashes"]:
                    column.append(Socket(plug))
                set = SocketSet(Socket(socket['plugHash']), column)
                itemSocketSet["sockets"].append(set)
    item.sockets = itemSocketSet["sockets"]


def getCharacterInfo(session, membershiptype, membershipid, characters):
    WCP = Manifest.getDatabaseConnection()
    charIDs = characters
    characterinfo = CharacterList()
    for char in charIDs:
        a = Character(char)
        result = getCharacter(session, membershiptype, membershipid, char, '200')
        a.emblemBackgroundPath = result['character']['data']['emblemBackgroundPath']
        a.light = result['character']['data']['light']
        classid = Manifest.HashtoID(result['character']['data']['classHash'])
        a.classname = WCP.selectQuery(classid, 'DestinyClassDefinition')['displayProperties']['name']
        raceid = Manifest.HashtoID(result['character']['data']['raceHash'])
        a.racename = WCP.selectQuery(raceid, 'DestinyRaceDefinition')['displayProperties']['name']
        genderid = Manifest.HashtoID(result['character']['data']['genderHash'])
        a.gendername = WCP.selectQuery(genderid, 'DestinyGenderDefinition')['displayProperties']['name']
        characterinfo.chars.append(a)
    return characterinfo


def validateLoadout(LoadoutObject):
    items = LoadoutObject
    exoticWeapon = 0
    exoticArmor = 0
    for item in items:
        if item['inventory']['tierTypeName'] == "Exotic":
            if item['inventory']['bucketTypeHash'] in [BUCKET_TYPE['Kinetic Weapons'],
                                                BUCKET_TYPE['Energy Weapons'],
                                                BUCKET_TYPE['Power Weapons']]:
                exoticWeapon += 1
            if item['inventory']['bucketTypeHash'] in [BUCKET_TYPE['Helmet'],
                                                BUCKET_TYPE['Gauntlets'],
                                                BUCKET_TYPE['Chest Armor'],
                                                BUCKET_TYPE['Leg Armor'],
                                                BUCKET_TYPE['Class Armor']]:
                exoticArmor += 1
    if (exoticWeapon > 1) or (exoticArmor > 1):
        return False
    else:
        return True


def equipLoadout(session, membershiptype, membershipid, LoadoutObject):
    target = LoadoutObject.characterid
    equippable = []
    transferdance = {}
    equippedelsewhere = {}
    invault = []
    # Find all the items
    for item in json.loads(LoadoutObject.loadout):
        response = getItem(session, membershiptype, membershipid,
                           item['itemInstanceId'], COMPONENTS['ItemCommonData'] + ',' + COMPONENTS['ItemInstances'])
        if response:
            if 'characterId' in response:
                if response['characterId'] == str(target):
                    if response['item']['data']['transferStatus'] == 1:
                        print('Already there buddy good to go')
                    elif response['item']['data']['transferStatus'] == 0 and response['instance']['data']['canEquip']:
                        print('carried but unequipped')
                        equippable.append(item)
                    else:
                        raise EquipError('Not on, on me, cant equip')
                else:  # on another character
                    if response['item']['data']['transferStatus'] == 0:
                        print('On another Character, transferable')
                        if response['characterId'] in transferdance:
                            transferdance[response['characterId']].append(item)
                        else:
                            transferdance[response['characterId']] = []
                            transferdance[response['characterId']].append(item)
                    if response['item']['data']['transferStatus'] == 1:
                        print('On another character, equipped')
                        if response['characterId'] in equippedelsewhere:
                            equippedelsewhere[response['characterId']].append(item)
                        else:
                            equippedelsewhere[response['characterId']] = []
                            equippedelsewhere[response['characterId']].append(item)
                    if response['item']['data']['transferStatus'] == 4:
                        print('On another character, vault full')
                        raise TransferError('Vault is Full, please clean space for DestinyLoadouts operation')
            else:
                print('ITEM IN Vault')
                invault.append(item)
        else:
            raise ItemNotFound('The Item requested was not found in the API response')

    #Start the equipping
    for item in equippable:
        equipItem(session, item['itemInstanceId'], target, membershiptype)
    for char in transferdance:
        for item in transferdance[char]:
            transferItem(session, membershiptype, char, item['itemHash'], item['itemInstanceId'], 1, True)
            transferItem(session, membershiptype, target, item['itemHash'], item['itemInstanceId'], 1, False)
            equipItem(session, item['itemInstanceId'], target, membershiptype)
    for item in invault:
        transferItem(session, membershiptype, target, item['itemHash'], item['itemInstanceId'], 1, False)
        equipItem(session, item['itemInstanceId'], target, membershiptype)
    for char in equippedelsewhere:
        for item in equippedelsewhere[char]:
            carrieditems = getCharacter(session, membershiptype, membershipid, char, COMPONENTS['CharacterInventories'])
            a = ''
            try:
                for i in carrieditems['inventory']['data']['items']:
                    if item['inventory']['bucketTypeHash'] in i.values():
                        a = i
            except KeyError:
                print('Access to Inventory Restricted')
                continue
            equipItem(session, a['itemInstanceId'], char, membershiptype)
            transferItem(session, membershiptype, char, item['itemHash'], item['itemInstanceId'], 1, True)
            transferItem(session, membershiptype, target, item['itemHash'], item['itemInstanceId'], 1, False)
            equipItem(session, item['itemInstanceId'], target, membershiptype)
    return


'''
Destiny Object Classes

Data structures to load API responses easier.
'''


class Item:
    def __init__(self, itemHash, itemInstanceId, sockets=None, displayProperties=None, inventory=None,categories=None, stats=None, manifestId=None):
        self.itemHash = itemHash
        self.itemInstanceId = itemInstanceId
        self.manifestId = manifestId if manifestId else Manifest.HashtoID(itemHash)
        self.displayProperties = displayProperties
        self.inventory = inventory
        self.categories = categories
        self.stats = stats if isinstance(stats, dict) else dict()
        self.sockets = []
        if sockets:
            for a in sockets:
                if isinstance(a,SocketSet):
                    self.sockets.append(a)
                else:
                    sockets.append(SocketSet(**a))
        if not all((self.manifestId, self.displayProperties, self.inventory, self.categories)):
            self.queryManifest()

    def __repr__(self):
        return '<Item %r>' % self.itemHash

    def queryManifest(self):
        wcp = Manifest.getDatabaseConnection()
        definition = wcp.selectQuery(self.manifestId, 'DestinyInventoryItemDefinition')
        self.displayProperties = definition['displayProperties']
        self.inventory = definition['inventory']
        self.categories = definition['itemCategoryHashes'] if 'itemCategoryHashes' in definition else []

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class Socket:
    def __init__(self,plugHash, manifestId=None, displayProperties=None):
        self.plugHash = plugHash
        self.manifestId= manifestId
        self.displayProperties = displayProperties
        if not all((self.manifestId, self.displayProperties)):
            self.manifestId = Manifest.HashtoID(plugHash)
            self.queryManifest()

    def __repr__(self):
        return '<Socket %r>' % self.plugHash

    def queryManifest(self):
        wcp = Manifest.getDatabaseConnection()
        definition = wcp.selectQuery(self.manifestId, 'DestinyInventoryItemDefinition')
        self.displayProperties = definition['displayProperties']


class SocketSet:
  def __init__(self, activeSocket, reusableSockets):
    self.activeSocket = activeSocket if isinstance(activeSocket, Socket) else Socket(**activeSocket)
    self.reusableSockets = []
    for a in reusableSockets:
       if isinstance(a,Socket):
         self.reusableSockets.append(a)
       else:
         self.reusableSockets.append(Socket(**a))


class Character:
  def __init__(self, charid, light='', classname='', racename='', gendername='', emblemBackgroundPath = ''):
    self.charid = charid
    self.light = light
    self.classname = classname
    self.racename = racename
    self.gendername = gendername
    self.emblemBackgroundPath = emblemBackgroundPath
  def __repr__(self):
    return '<Character %s>' % (str(self.light) + ' ' + self.classname)


class CharacterList:
    def __init__(self, chars=[]):
        self.chars = [Character(**char) for char in chars]

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class Inventory:
    def __init__(self, membershipId, kinetic=[], energy=[], power=[], hunterArmor={}, warlockArmor={}, titanArmor={}):
        self.membershipId = membershipId
        self.kinetic = [Item(**item) for item in kinetic]
        self.energy = [Item(**item) for item in energy]
        self.power = [Item(**item) for item in power]
        self.hunterArmor = {armor: [] for armor in ARMOR_TYPES}
        for a in ARMOR_TYPES:
            if a in hunterArmor:
                self.hunterArmor[a] = [Item(**item) for item in hunterArmor[a]]
        self.warlockArmor = {armor: [] for armor in ARMOR_TYPES}
        for a in ARMOR_TYPES:
            if a in warlockArmor:
                self.warlockArmor[a] = [Item(**item) for item in warlockArmor[a]]
        self.titanArmor = {armor: [] for armor in ARMOR_TYPES}
        for a in ARMOR_TYPES:
            if a in titanArmor:
                self.titanArmor[a] = [Item(**item) for item in titanArmor[a]]

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)



'''
Destiny Exceptions

Custom Exception mappings
'''


class DestinyException(Exception):
  """Base custom exception class"""
  pass


class APIError(DestinyException):
  """Raised when API cannot be reached"""
  pass


class TransferError(DestinyException):
  """Raised when item cannot transfer"""
  pass


class EquipError(DestinyException):
  """raised when equip logic fails"""


class ItemNotFound(DestinyException):
  """raised when getItem returns a 404"""
  pass

