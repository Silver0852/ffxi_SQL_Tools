import sqlalchemy as sa

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
#from tksFlags import * 
import os
from datetime import datetime
#Module Globals

if os.name == 'posix':
    engine = sa.create_engine('postgresql:///ffxidb')
    Base = declarative_base(bind=engine)
    cnnf =sessionmaker(bind=engine)
else:
    engine = sa.create_engine('mssql+pyodbc://127.0.0.1\\SQLEXPRESS/ffxi?driver=SQL+Server+Native+Client+11.0')
    Base = declarative_base(bind=engine)
    cnnf = sessionmaker(bind=engine)

# Table Classes
class knownEntities(Base):
    __tablename__ = 'knownEntities'
    rowid = sa.Column(sa.Integer, primary_key=True)
    entityId = sa.Column(sa.Integer)
    entityType = sa.Column(sa.Integer)
    entityName = sa.Column(sa.String)
    playerId = sa.Column(sa.Integer)
    serverId = sa.Column(sa.Integer)

class players(Base):
    __tablename__ = 'Players'
    rowid = sa.Column(sa.Integer, primary_key=True)
    observedInternalXI_Id = sa.Column(sa.String)
    ffxiah_id = sa.Column(sa.Integer)
    playerName = sa.Column(sa.String)
    serverId = sa.Column(sa.Integer)
    accountId = sa.Column(sa.Integer, sa.ForeignKey('Accounts.rowid'),default=0)
    account = relationship('accounts')
    monitorMode = sa.Column(sa.Boolean, default=False)
    def __repr__(self):
        return 'RowId: %s, playerName: %s' % (self.rowid, self.playerName)

class accounts(Base):
    __tablename__ = 'Accounts'
    rowid = sa.Column(sa.Integer, primary_key=True)
    POL_ID = sa.Column(sa.String(250))
    def __repr__(self):
        return 'ID: %s PolID: %s' % (self.rowid, self.POL_ID)

class playerEquipped(Base):
    __tablename__ = 'playerEquippedLast'
    rowid = sa.Column(sa.Integer, primary_key=True)
    slot = sa.Column(sa.Integer)
    itemId = sa.Column(sa.Integer)
    updatedByPacketId = sa.Column(sa.Integer)
    updatedByPacketType = sa.Column(sa.String)

#class playerInventory(Base):
#    __tablename__ = 'inventoryLast'
#    rowid = sa.Column(sa.Integer, primary_key=True)
#    bag = sa.Column(sa.Integer)
#    Index = sa.Column(sa.Integer)
#    ItemId = sa.Column(sa.Integer)
#    ItemCount = sa.Column(sa.Integer)
#    itemExtData = sa.Column(sa.Binary)
#    PlayerId = sa.Column(sa.Integer, sa.ForeignKey('Players.rowid'))
#    player = relationship('players')
#    updatedByPacketId = sa.Column(sa.Integer)
    
#    def __repr__(self):
#        return '<bag> %s <idx> %s <count> %s <itemId> %s' % (self.bag, self.Index, self.ItemCount, self.ItemId)

class servers(Base):
    __tablename__ = 'servers'
    rowid = sa.Column(sa.Integer, primary_key = True)
    server_name = sa.Column(sa.String(250))
    isActive = sa.Column(sa.Integer)
    def __repr__(self):
        return 'ID: %s, server name: %s, isactive: %s' % (self.rowid, self.server_name, self.isActive)

class sales(Base):
    __tablename__ = 'sale'
    rowid = sa.Column(sa.Integer, primary_key = True)
    sTimeStamp = sa.Column(sa.DateTime)
    itemId = sa.Column(sa.Integer)
    sellerId = sa.Column(sa.Integer)
    buyerId = sa.Column(sa.Integer)
    price = sa.Column(sa.Integer)
    stack = sa.Column(sa.Integer)
    def __repr__(self):
        return 'ID: %s, itemId: %s, Seller: %s, Buyer: %s, price: %s' % (self.rowid, self.itemId, self.sellerId, self.buyerId, self.price)

class ffxiah_scanHistory(Base):
    __tablename__ = 'ffxiah_scanHistory'
    rowid = sa.Column(sa.Integer, primary_key=True)
    scanType = sa.Column(sa.String) #alter table ffxiah_scanHistory add type[varchar](50)
    itemId = sa.Column(sa.Integer)
    scanTimestamp = sa.Column(sa.DateTime)#alter table ffxiah_scanHistory alter column scanTimestamp[datetime]
    newSaleCount = sa.Column(sa.Integer)
    lastSaleTimestamp = sa.Column(sa.DateTime)#alter table ffxiah_scanHistory alter column lastSaleTimestamp[datetime]
    def __repr__(self):
        return '<itemId>: %s <scanTimestamp>: %s' % (self.itemId, self.scanTimestamp)

class ffxiah_scanObjectConfig(Base):
    __tablename__ = 'ffxiah_scanObjectConfig'
    rowid = sa.Column(sa.Integer, primary_key=True)
    objectType = sa.Column(sa.String) # item vs player #alter table ffxiah_scanobjectconfig alter column objecttype[varchar](50)
    objectId = sa.Column(sa.Integer) # item ID, (player id, item id)
    lastScan = sa.Column(sa.DateTime)
    nextScan = sa.Column(sa.DateTime) # 
    timeSlice = sa.Column(sa.Integer) # timeslice in seconds, calculated via metadata
    def __repr__(self):
        return '<ID> %s, <ObjectType> %s, <ScanFrequency> %s' % (self.rowid, self.objectType, self.timeSlice)


class ffxiah_scanGlobalConfig(Base):
    __tablename__ = 'ffxiah_scanGlobalConfig'
    rowid = sa.Column(sa.Integer, primary_key = True)
    configKey = sa.Column(sa.String)
    configValue = sa.Column(sa.String)
    dataType = sa.Column(sa.String) #alter table ffxiah_scanGlobalConfig add dataType[varchar](10)
    def __repr__(self):
        return '<%s> %s' % (self.configKey, self.configValue)

#{"id", "en", "ja", "enl", "jal", "category", "flags", "stack", "targets", "type", "cast_time", 
#"jobs", "level", "races", "slots", "cast_delay", "max_charges", "recast_delay", "shield_size", 
#"damage", "delay", "skill", "item_level", "superior_level"}
class baseItems(Base):
    __tablename__ = 'items'
    rowid = sa.Column(sa.Integer, primary_key=True)
    itemNameEnglish = sa.Column(sa.String)
    itemLogName = sa.Column(sa.String)#
    category = sa.Column(sa.String)
    flags = sa.Column(sa.Integer)
    stackSize = sa.Column(sa.Integer)
    targets = sa.Column(sa.Integer)
    type = sa.Column(sa.Integer)
    castTime = sa.Column(sa.Float)
    jobs = sa.Column(sa.Integer)
    level = sa.Column(sa.Integer)
    races = sa.Column(sa.Integer)
    slots = sa.Column(sa.Integer)
    castDelay = sa.Column(sa.Float)
    maxCharges = sa.Column(sa.Integer)
    recastDelay = sa.Column(sa.Float)
    shieldSize = sa.Column(sa.Integer)
    damage = sa.Column(sa.Integer)
    delay = sa.Column(sa.Integer)
    skill = sa.Column(sa.Integer)
    itemLevel = sa.Column(sa.Integer)
    superiorLevel = sa.Column(sa.Integer)
    def __repr__(self):
        return '<ItemID> %s <ItemNameEnglish> %s' % (self.rowid, self.itemNameEnglish)

class ItemDesc(Base):
    __tablename__ = 'itemDescriptions'
    rowid = sa.Column(sa.Integer, primary_key=True)
    Description = sa.Column(sa.String)
    DescriptorSplits = sa.Column(sa.String)
    def __repr__(self):
        return '<ItemId> %s <Descrition> %s <Descriptors> %s' % (self.rowid, self.Description, self.DescriptorSplits)

class ItemEffects(Base):
    __tablename__ = 'itemEffects'
    rowid = sa.Column(sa.Integer, primary_key=True)
    effectText = sa.Column(sa.String)
    effectExt = sa.Column(sa.String)
    def __repr__(self):
        pass

class ItemEffectAssociation(Base):
    __tablename__ = 'ItemEffectAssociations'
    rowid = sa.Column(sa.Integer, primary_key=True)
    itemId = sa.Column(sa.Integer)
    effectDescriptor = sa.Column(sa.String)
    effectValue = sa.Column(sa.Integer)
    effectFunc = sa.Column(sa.String)
    effectClass = sa.Column(sa.String)
    def __repr__(self):
        pass

class ItemSlips(Base):
    __tablename__ = 'itemSlips'
    rowid = sa.Column(sa.Integer, primary_key=True)
    slipItemId = sa.Column(sa.Integer) #item id of the slip itself
    ordinal = sa.Column(sa.Integer) #ordinal position 0 indexed unique to slip
    storableId = sa.Column(sa.Integer) #storable item id
    def __repr__(self):
        pass

class packetData(Base):
    __tablename__ = 'xiPacketData'
    rowid =sa.Column(sa.Integer, primary_key=True)
    fileId = sa.Column(sa.Integer, sa.ForeignKey('xiPacketFile.rowid'))
    file = relationship("packetFiles")
    direction  = sa.Column(sa.Integer)
    pktTimeStamp = sa.Column(sa.DateTime)
    pktTypeId = sa.Column(sa.Integer)
    pktAshitaSize = sa.Column(sa.Integer)
    pktOffset = sa.Column(sa.Integer)
    pktPayload = sa.Column(sa.LargeBinary)
    playerId = sa.Column(sa.Integer, sa.ForeignKey('Players.rowid'))
    player = relationship('players')
    def __repr__(self):
        return 'rowid: %s type: %s size: %s direction: %s' % (self.rowid, self.pktTypeId, self.pktAshitaSize, self.direction)
    
class packetFiles(Base):
    __tablename__ = 'xiPacketFile'
    rowid = sa.Column(sa.Integer, primary_key=True)
    filename = sa.Column(sa.String)
    createDate = sa.Column(sa.DateTime)
    closeDate = sa.Column(sa.DateTime) # must be created on update, cannot be set during creation
    fileLength = sa.Column(sa.Integer)
    payload = sa.Column(sa.LargeBinary)
    def __repr__(self):
        return 'rowid: %s filename: %s fileLength: %s' % (self.rowid, self.filename, self.fileLength)

class packetTemplates(Base):
    __tablename__ = 'xiPacketTemplate'
    rowid = sa.Column(sa.Integer, primary_key = True)
    direction = sa.Column(sa.Integer)
    typeId = sa.Column(sa.Integer)
    struct = sa.Column(sa.String)
    size = sa.Column(sa.Integer)
    name = sa.Column(sa.String)
    src = sa.Column(sa.String)
    notes = sa.Column(sa.String)
    def __repr__(self):
        return '<rowid> %s <name> %s <notes> %s <struct string> \'%s\' <default size> %s' % (self.rowid, self.name ,self.notes, self.struct, self.size)

class playerStats(Base):
    __tablename__ = 'playerStats'
    rowid = sa.Column(sa.Integer, primary_key=True)
    playerid = sa.Column(sa.Integer, sa.ForeignKey('Players.rowid'))
    player = relationship('players')
    str = sa.Column(sa.Integer)
    dex = sa.Column(sa.Integer)
    agi = sa.Column(sa.Integer)
    int = sa.Column(sa.Integer)
    mnd = sa.Column(sa.Integer)
    vit = sa.Column(sa.Integer)
    chr = sa.Column(sa.Integer)
    def __repr__(self):
        return '<rowid> %s' % self.rowid

class zoneId(Base):
    __tablename__='zoneIds'
    rowid = sa.Column(sa.Integer, primary_key=True)
    zoneName = sa.Column(sa.String)
    regionName = sa.Column(sa.String)
    def __repr__(self):
        return '<rowid>: %s-- %s.%s' % (self.rowid, self.regionName, self.zoneName)

class playerCurrencie(Base):
    __tablename__ = 'playerCurrencies'
    rowid = sa.Column(sa.Integer, primary_key = True)
    playerId = sa.Column(sa.Integer, sa.ForeignKey('Players.rowid'))
    player = relationship('players')
    sandoria_cp = sa.Column(sa.Integer, default=0)
    bastok_cp = sa.Column(sa.Integer, default=0)
    windurst_cp = sa.Column(sa.Integer, default=0)
    beastman_seal = sa.Column(sa.Integer, default=0)
    kindred_seal = sa.Column(sa.Integer, default=0)
    kindred_crest = sa.Column(sa.Integer, default=0)
    high_kindred_crest = sa.Column(sa.Integer, default=0)
    sacred_kindred_crest = sa.Column(sa.Integer, default=0)
    ancient_beastcoin = sa.Column(sa.Integer, default=0)
    valor_point = sa.Column(sa.Integer, default=0)
    scyld = sa.Column(sa.Integer, default=0)
    guild_fishing = sa.Column(sa.Integer, default=0)
    guild_woodworking = sa.Column(sa.Integer, default=0)
    guild_smithing = sa.Column(sa.Integer, default=0)
    guild_goldsmithing = sa.Column(sa.Integer, default=0)
    guild_weaving = sa.Column(sa.Integer, default=0)
    guild_leathercraft = sa.Column(sa.Integer, default=0)
    guild_bonecraft = sa.Column(sa.Integer, default=0)
    guild_alchemy = sa.Column(sa.Integer, default=0)
    guild_cooking = sa.Column(sa.Integer, default=0)
    cinder = sa.Column(sa.Integer, default=0)
    fire_fewell = sa.Column(sa.Integer, default=0)
    ice_fewell = sa.Column(sa.Integer, default=0)
    wind_fewell = sa.Column(sa.Integer, default=0)
    earth_fewell = sa.Column(sa.Integer, default=0)
    lightning_fewell = sa.Column(sa.Integer, default=0)
    water_fewell = sa.Column(sa.Integer, default=0)
    light_fewell = sa.Column(sa.Integer, default=0)
    dark_fewell = sa.Column(sa.Integer, default=0)
    ballista_point = sa.Column(sa.Integer, default=0)
    fellow_point = sa.Column(sa.Integer, default=0)
    chocobuck_sandoria = sa.Column(sa.Integer, default=0)
    chocobuck_bastok = sa.Column(sa.Integer, default=0)
    chocobuck_windurst = sa.Column(sa.Integer, default=0)
    research_mark = sa.Column(sa.Integer, default=0)
    tunnel_worm = sa.Column(sa.Integer, default=0)
    morion_worm = sa.Column(sa.Integer, default=0)
    phantom_worm = sa.Column(sa.Integer, default=0)
    moblin_marble = sa.Column(sa.Integer, default=0)
    infamy = sa.Column(sa.Integer, default=0)
    prestige = sa.Column(sa.Integer, default=0)
    legion_point = sa.Column(sa.Integer, default=0)
    spark_of_eminence = sa.Column(sa.Integer, default=0)
    shining_star = sa.Column(sa.Integer, default=0)
    imperial_standing = sa.Column(sa.Integer, default=0)
    leujaoam_assault_point = sa.Column(sa.Integer, default=0)
    mamool_assault_point = sa.Column(sa.Integer, default=0)
    lebros_assault_point = sa.Column(sa.Integer, default=0)
    periqia_assault_point = sa.Column(sa.Integer, default=0)
    ilrusi_assault_point = sa.Column(sa.Integer, default=0)
    nyzul_isle_assault_point = sa.Column(sa.Integer, default=0)
    zeni_point = sa.Column(sa.Integer, default=0)
    jetton = sa.Column(sa.Integer, default=0)
    therion_ichor = sa.Column(sa.Integer, default=0)
    allied_notes = sa.Column(sa.Integer, default=0)
    cruor = sa.Column(sa.Integer, default=0)
    resistance_credit = sa.Column(sa.Integer, default=0)
    dominion_note = sa.Column(sa.Integer, default=0)
    fifth_echelon_trophy = sa.Column(sa.Integer, default=0)
    fourth_echelon_trophy = sa.Column(sa.Integer, default=0)
    third_echelon_trophy = sa.Column(sa.Integer, default=0)
    second_echelon_trophy = sa.Column(sa.Integer, default=0)
    first_echelon_trophy = sa.Column(sa.Integer, default=0)
    cave_points = sa.Column(sa.Integer, default=0)
    id_tags = sa.Column(sa.Integer, default=0)
    op_credits = sa.Column(sa.Integer, default=0)
    traverser_stones = sa.Column(sa.Integer, default=0)
    voidstones = sa.Column(sa.Integer, default=0)
    kupofried_corundums = sa.Column(sa.Integer, default=0)
    pheromone_sacks = sa.Column(sa.Integer, default=0)

class recipe(Base):
    __tablename__ = 'recipes'
    rowid = sa.Column(sa.Integer, primary_key = True)
    requiredKeyItem = sa.Column(sa.Integer)
    NQ = sa.Column(sa.Integer, default=0)
    NQCount= sa.Column(sa.Integer, default=0)
    HQ1 = sa.Column(sa.Integer, default=0)
    HQ1Count = sa.Column(sa.Integer, default=0)
    HQ2 = sa.Column(sa.Integer, default=0)
    HQ2Count = sa.Column(sa.Integer, default=0)
    HQ3 = sa.Column(sa.Integer, default=0)
    HQ3Count = sa.Column(sa.Integer, default=0)
    Crystal= sa.Column(sa.Integer, default=0)
    Ingr1 = sa.Column(sa.Integer, default=0)
    Ingr2 = sa.Column(sa.Integer, default=0)
    Ingr3 = sa.Column(sa.Integer, default=0)
    Ingr4 = sa.Column(sa.Integer, default=0)
    Ingr5 = sa.Column(sa.Integer, default=0)
    Ingr6 = sa.Column(sa.Integer, default=0)
    Ingr7 = sa.Column(sa.Integer, default=0)
    Ingr8 = sa.Column(sa.Integer, default=0)
    capFishing = sa.Column(sa.Integer, default=0)
    capWoodworking = sa.Column(sa.Integer, default=0)
    capSmithing = sa.Column(sa.Integer, default=0)
    capGoldsmithing = sa.Column(sa.Integer, default=0)
    capClotchcraft = sa.Column(sa.Integer, default=0)
    capLeathercraft = sa.Column(sa.Integer, default=0)
    capBonecraft = sa.Column(sa.Integer, default=0)
    capAlchemy = sa.Column(sa.Integer, default=0)
    capCooking = sa.Column(sa.Integer, default=0)
    capSynergy = sa.Column(sa.Integer, default=0)
    confirmed = sa.Column(sa.Boolean, default=False)
    recipeName = sa.Column(sa.String, default='')  #alter table recipes add recipeName [varchar](250)
    def __repr__(self):
        return ''

class craftHistory(Base):
    __tablename__='craftHistory'
    rowid = sa.Column(sa.Integer, primary_key=True)
    recipeId = sa.Column(sa.Integer)
    playerId = sa.Column(sa.Integer)
    resultTier = sa.Column(sa.Integer)
    resultItemId = sa.Column(sa.Integer)
    resultQty = sa.Column(sa.Integer)
    def __repr__(Base):
        return ''

class resourceFiles(Base):
    __tablename__ = 'resourceFiles'
    rowid = sa.Column(sa.Integer, primary_key=True)
    filepath = sa.Column(sa.String)
    fileHash = sa.Column(sa.String)
    observationDate = sa.Column(sa.String)
    fileSize = sa.Column(sa.Integer)
    contentType = sa.Column(sa.String, default='Unknown')
    encryptionMethod = sa.Column(sa.String, default='Unknown')
    snippet = sa.Column(sa.LargeBinary)
    def __repr__(self):
        return '<rowid> %s <path> %s <size> %s <hash> %s' % (self.rowid, self.filepath, self.fileSize, self.fileHash)

class notes(Base):
    __tablename__ = 'notes'
    rowid = sa.Column(sa.Integer, primary_key=True)
    entityType= sa.Column(sa.String)
    entityId = sa.Column(sa.Integer)
    note = sa.Column(sa.String)
    
class gpHistory(Base):
    __tablename__ = 'gpHistory'
    rowid = sa.Column(sa.Integer, primary_key=True)
    gpDate = sa.Column(sa.Date)
    craft = sa.Column(sa.String)  #alter table gpHistory alter column craft[varchar](50)
    guildRank = sa.Column(sa.String) #alter table gpHistory alter column guildRank[varchar](50)
    guildRankNum =sa.Column(sa.Integer) #alter table gpHistory add guildRankNum[int]
    itemid = sa.Column(sa.Integer)
    def __repr__(self):
        return '<rowid> %s <Date> %s <Craft> %s <Rank> %s <ItemId> %s' % (self.rowid, self.gpDate, self.craft, self.guildRank, self.itemid )

class itemExt(Base):
    __tablename__ = 'itemExt'
    rowid = sa.Column(sa.Integer, primary_key=True) #item id
    gpValue = sa.Column(sa.Integer)
    gpMaxValue = sa.Column(sa.Integer)
    gpMaxCount = sa.Column(sa.Integer)
    bgWikiLink = sa.Column(sa.String) #alter table itemext add bgWikiLink[varchar](250);
    xiahLink = sa.Column(sa.String)#alter table itemext add xiahLink[varchar](250)
    stdNPC_Val = sa.Column(sa.Integer)#alter table itemExt add stdNPC_Val[int]
    stdGuildType = sa.Column(sa.String)#alter table itemExt add stdGuildType[varchar](50)
    stdGildValMin = sa.Column(sa.Integer)#alter table itemExt add stdGuildValMin[int]
    stdGuildValMax = sa.Column(sa.Integer)#alter table itemExt add stdGuildValMax[int]
    sortTo = sa.Column(sa.Integer)#alter table itemExt add sortTo[int] --playerid
    sparks = sa.Column(sa.Integer)#alter table itemExt add sparks[int]
    def __repr__(self):
        return '<itemId> %s <gpVal> %s <maxVal> %s <maxCount> %s <bg-wiki> %s' % ( self.rowid, self.gpValue, self.gpMaxValue, self.gpMaxCount, self.bgWikiLink)

class playerInventory(Base):
    __tablename__ = 'playerInventories'
    rowid = sa.Column(sa.Integer, primary_key=True)
    playerId = sa.Column(sa.Integer)
    storageIdx = sa.Column(sa.Integer)
    storageTxt = sa.Column(sa.String)
    slotIdx = sa.Column(sa.Integer)
    itemId = sa.Column(sa.Integer)
    qty = sa.Column(sa.Integer)
    lastSeen = sa.Column(sa.DateTime)
    src = sa.Column(sa.String)
    equipFlag = sa.Column(sa.Boolean) #alter table playerInventories add equipFlag[smallint]
    extData =sa.Column(sa.LargeBinary)#alter table playerInventories add extData[varbinary](max)
    extDataText = sa.Column(sa.String) #alter table playerInvetories add extDataText[varchar](250)
    def __repr__(self):
        return ''

class playerCrafts(Base):
    __tablename__ = 'playerCrafts'
    rowid = sa.Column(sa.Integer, primary_key=True)
    playerId = sa.Column(sa.Integer)
    alcSkill= sa.Column(sa.Integer)
    alcRank= sa.Column(sa.String)
    boneSkill= sa.Column(sa.Integer)
    boneRank= sa.Column(sa.String)
    clothSkill= sa.Column(sa.Integer)
    clothRank= sa.Column(sa.String)
    cookSkill= sa.Column(sa.Integer)
    cookRank= sa.Column(sa.String)
    fishSkill= sa.Column(sa.Integer)
    fishRank= sa.Column(sa.String)
    goldSkill= sa.Column(sa.Integer)
    goldRank= sa.Column(sa.String)
    leatherSkill= sa.Column(sa.Integer)
    leatherRank= sa.Column(sa.String)
    smithSkill= sa.Column(sa.Integer)
    smithRank= sa.Column(sa.String)
    woodSkill= sa.Column(sa.Integer)
    woodRank= sa.Column(sa.String)
    synergySkill = sa.Column(sa.Integer)
    synergyRank = sa.Column(sa.String)
    def __repr__(self):
        return '<player>: %s <alc> %s-%s <bone> %s-%s <cloth> %s-%s <cooking> %s-%s <fishing> %s-%s <gold> %s-%s <leather> %s-%s <smith> %s-%s <wood> %s-%s <synergy> %s-%s' % (self.alcSkill, self.alcRank, self.boneSkill, self.boneRank,self.clothSkill, self.clothRank, self.cookSkill, self.cookRank, self.fishSkill, self.fishRank,self.goldSkill, self.goldRank, self.leatherSkill, self.leatherRank, self.smithSkill, self.smithRank, self.woodSkill, self.woodRank, self.synergySkill, self.synergyRank)

class playerGpHistory(Base):
    __tablename__ = 'playerGpHistory'
    rowid = sa.Column(sa.Integer, primary_key=True)
    playerId = sa.Column(sa.Integer)
    gpDate = sa.Column(sa.Date)
    gpPercentComplete = sa.Column(sa.Integer)
    gpStartVal = sa.Column(sa.Integer)
    gpEndVal = sa.Column(sa.Integer)
    gpHistoryRec = sa.Column(sa.Integer)
    def __repr__(self):
        return ''

class fishKnown(Base):
    __tablename__ ='fishKnown'
    rowid = sa.Column(sa.Integer, primary_key=True)
    xi1_id = sa.Column(sa.Integer)
    xi2_id = sa.Column(sa.Integer)
    xi3_id = sa.Column(sa.Integer)
    baitItemId = sa.Column(sa.Integer)
    itemId = sa.Column(sa.Integer)
    zoneId = sa.Column(sa.Integer)
    rodId = sa.Column(sa.Integer)
    quantity = sa.Column(sa.Integer) #alter table fishKnown add quantity[int]
    def __repr__(self):
        return '<zone> %s <fish> %s <rod> %s <bait> %s <id1-2-3> %s-%s-%s' % (self.zoneId, self.itemId, self.rodId, self.baitItemId, self.xi1_id, self.xi2_id, self.xi3_id)

class fishHistory(Base):
    __tablename__ = 'fishHistory'
    rowid = sa.Column(sa.Integer, primary_key=True)
    itemId = sa.Column(sa.Integer)
    playerId = sa.Column(sa.Integer)
    posX = sa.Column(sa.Float)
    posY = sa.Column(sa.Float)
    posZ = sa.Column(sa.Float)
    zoneId = sa.Column(sa.Integer)
    baitId = sa.Column(sa.Integer)
    rodId = sa.Column(sa.Integer)
    xi1_Id = sa.Column(sa.Integer)
    xi2_Id = sa.Column(sa.Integer)
    xi3_Id = sa.Column(sa.Integer)
    def __repr__(self):
        return '<rowid> %s' % self.rowid

#Support Tables

class craftRankItems(Base):
    __tablename__ = 'craftRankItems'
    rowid = sa.Column(sa.Integer, primary_key = True)
    craft = sa.Column(sa.String)
    craftRankTo = sa.Column(sa.String)
    itemId = sa.Column(sa.Integer)
    def __repr__(self):
        return '<craft> %s <rank to> %s <itemid> %s' % (self.craft, self.craftRankTo, self.itemId)


class skillCapLevels(Base):
    __tablename__ = 'skillCapLevels'
    rowid = sa.Column(sa.Integer, primary_key = True)
    job = sa.Column(sa.Integer)
    skill = sa.Column(sa.Integer)
    jobLevel = sa.Column(sa.Integer)
    def __repr__(self):
        return '<job> %s <skill> %s <level> %s' % (self.job, self.skill, self.jobLevel)


#helper methods

def getCharacterReference(session, char):
    qObj = session.query(players).filter(players.playerName==char)
    if qObj.count() > 1:
        pass #error
    elif qObj.count() == 0:
        p = players(playerName = char)
        session.add(p)
        session.commit()
        return p
    else:
        return qObj.first()

def getFileReference(session, fileName, fileBase):
    qObj = session.query(packetFiles).filter(packetFiles.filename == fileName)
    if qObj.count() == 0:
        file = packetFiles()
        file.filename = fileName
        #file.payload =  open(os.path.join(fileBase, fileName),'rb').read()
        file.payload = None
        file.fileLength = 0 #len(file.payload)
        session.add(file)
        session.commit()
        return file
    else:
        return qObj.first()

def addSales(saleItems, session, itemId, stack):
    insertItemCount = 0
    insertPlayerCount = 0
    lastSale = datetime.fromordinal(1)
    for item in saleItems:
        buyer = item['buyer']
        seller = item['seller']
        ts = datetime.fromtimestamp( item['saleon'])
        ct = session.query(sales).filter(sa.and_(sales.sTimeStamp==ts.strftime('%Y-%m-%d %H:%M:%S'), sales.buyerId==buyer, sales.sellerId==seller, sales.itemId==itemId)).count()
        if ts > lastSale:
            lastSale = ts
        if ct == 0:
            s = sales()
            s.buyerId = buyer  
            s.sellerId = seller
            s.sTimeStamp = ts
            s.price = item['price']
            s.itemId = itemId
            s.stack = stack
            insertItemCount +=1
            session.add(s)
        ct = session.query(players).filter(players.ffxiah_id == buyer).count()
        if ct == 0:
            p = players()
            p.accountId = 0
            p.observedInternalXI_Id = 0
            p.ffxiah_id = buyer
            p.playerName = item['buyer_name']
            p.serverId = item['buyer_server']
            insertPlayerCount += 1
            session.add(p)
            session.commit()
        ct = session.query(players).filter(players.ffxiah_id == seller).count()
        if ct == 0:
            p2 = players()
            p2.accountId = 0
            p2.observedInternalXI_Id = 0
            p2.ffxiah_id = seller
            p2.playerName = item['seller_name']
            p2.serverId = item['seller_server']
            insertPlayerCount += 1
            session.add(p2)
            session.commit()
    session.commit()
    sh = ffxiah_scanHistory()
    sh.itemId = itemId
    sh.lastSaleTimestamp = lastSale
    sh.scanTimestamp = datetime.now()
    sh.newSaleCount = insertItemCount
    sh.scanType = 'Item'
    session.add(sh)
    session.commit()
    return True, insertItemCount, insertPlayerCount

def addPlayerSales(saleItems, playerName, session):
    insertCount = 0
    lastSale = 0
    addPlayerCount = 0
    lastSale = datetime.fromordinal(1)
    if len(saleItems) == 0:
        return False
    for item in saleItems:
        
        s = sales()
        ts = datetime.fromtimestamp( item['saleon'])
        s.buyerId = item['buyer_id']
        s.sellerId = item['seller_id']
        s.price = item['price']
        s.itemId = item['int_id']
        if ts > lastSale:
            lastSale = ts
        if item['countof'] == 0:
            s.stack = 0
        else:
            s.stack = 1
        s.sTimeStamp = ts
        ct = session.query(sales).filter(sa.and_(sales.buyerId==s.buyerId, sales.sellerId==s.sellerId, sales.itemId==s.itemId, sales.stack==s.stack, sales.sTimeStamp==s.sTimeStamp)).count()
        if ct ==0:
            insertCount += 1
            session.add(s)
            session.commit()
        if session.query(players).filter(players.ffxiah_id==s.buyerId).count() ==0:
            p = players()
            p.monitorMode = 0
            p.accountId = 0
            p.ffxiah_id = int(item['buyer_id'])
            p.playerName = item['buyer_name']
            p.observedInternalXI_Id = 0
            p.serverId = 1
            p.monitorMode = 0
            p.accountId = 0
            addPlayerCount += 1
            session.add(p)
            session.commit()
            onetime = ffxiah_scanObjectConfig()
            onetime.lastScan = datetime.now()
            onetime.nextScan = datetime.now()
            onetime.timeSlice = 0
            onetime.objectId = int(item['buyer_id'])
            onetime.objectType = 'Player'
            session.add(onetime)
            session.commit()
        if session.query(players).filter(players.ffxiah_id==s.sellerId).count() == 0:
            p = players()
            p.monitorMode = 0
            p.accountId = 0
            p.ffxiah_id = int(item['seller_id'])
            p.playerName = item['seller_name']
            p.observedInternalXI_Id = 0
            p.serverId = 1
            p.monitorMode = 0
            addPlayerCount += 1
            session.add(p)
            session.commit()
            onetime = ffxiah_scanObjectConfig()
            onetime.lastScan = datetime.now()
            onetime.nextScan = datetime.now()
            onetime.timeSlice = 0
            onetime.objectId = int(item['seller_id'])
            onetime.objectType = 'Player'
            session.add(onetime)
            session.commit()
    sh = ffxiah_scanHistory()
    sh.scanType = 'Player'
    if saleItems[0]['buyer_name'] == playerName:
        sh.itemId = int(saleItems[0]['buyer_id'])
    else:
        sh.itemId = int(saleItems[0]['seller_id'])
    sh.newSaleCount = insertCount
    sh.lastSaleTimestamp = lastSale
    sh.scanTimestamp = datetime.now()
    session.add(sh)
    session.commit()
    return True, insertCount, addPlayerCount

def getRecipe(session, primaryCraft=0,subCraft=0, itemId=0, limit=0):
    pass

def addRecipe(session, ingredientList, craftLevelList, keyItemList, expectedResultList=None):
    pass

def addRecipeFromPacket(pkt):
    pass


def printDebug(obj):
    if obj is dict:
        for item in obj.keys():
            print ('item = {%s: %s' % item, obj[item])
    else:
        print(obj)

def getItemIdByName(itemName):
    session = cnnf()
    obj = session.query(baseItems).filter(baseItems.itemNameEnglish==itemName).all()
    if len(obj) == 0:
        return None
    elif len(obj) > 1:
        return None
    else:
        return obj[0].rowid

#create tables
#Base.metadata.create_all(engine)
