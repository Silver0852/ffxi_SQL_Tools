import os
import ffxi_sql
import struct
import sys
import tksFlags
import ffxi_supportClasses
from pprint import pprint
from hexdump import hexdump

class ov(object):
    pass
#post processing filters
def nullTerminatedString(bString):
    if bString.find(b'\x00') >= 0:
        retString = bString[:bString.find(b'\x00')]
        return str(retString, encoding='utf-8')
    else:
        return str(bString, encoding='utf-8', errors='ignore')

def noFilter(val):
    return val

def binField(val):
    retString = bin(val)
    return retString

class field(object):    #must define hex filter still
    def __init__(self, start=0, length=0, postFilter=noFilter):
        self.start = start
        self.length = length
        self.prepend = '<'
        self.structString = self.prepend + str(length) + 's'
        
        self.postFilter = postFilter

    def getValue(self, payload, overridePostFilter=None):
        retVal = struct.unpack_from(self.structString, payload, self.start)[0]
        if overridePostFilter is not None:
            retVal = overridePostFilter(retVal)
        elif self.postFilter is not None:
            retVal = self.postFilter(retVal)
        return retVal

class string(field):
    def __init__(self, start=0, length=0, postFilter=noFilter):
        super().__init__(start=start, length=length, postFilter=postFilter)
    def getValue(self, payload):
        retVal = struct.unpack_from(self.structString, payload, self.start)[0]
        return self.postFilter(retVal)

class varString(field):
    def __init__(self, start=0, postFilter=nullTerminatedString):
        super().__init__(start=start, length=0, postFilter=postFilter)
    def getValue(self, payload):
        retVal = payload[self.start:]
        if retVal.find(b'\x00') < 0:
            return self.postFilter(retVal)
        else:
            return self.postFilter(retVal[:retVal.find(b'\x00')+1])


class jobGroup(field):
    def __init__(self, start=0, skip=1, count=22):
        super().__init__(start, count)
        self.count = count
        self.skip = skip
        self.structString = '<' + str(count) + 'B'

    def getValue(self, payload):
        structObj = struct.unpack_from(self.structString, payload, self.start)
        retList = []
        for i in range(self.count):
            retList.append((ffxi_supportClasses.jobs[i + self.skip], structObj[i]))
        return retList

class elementGroup(field):
    def __init__(self, start=0, skip=1, count=8):
        super().__init__(start, count)
        self.count = count
        self.skip = skip
        self.structString = '<' + str(count) + 'h'

    def getValue(self, payload):
        structObj = struct.unpack_from(self.structString, payload, self.start)
        retList = []
        for i in range(self.count):
            retList.append((ffxi_supportClasses.Elements[i+self.skip], structObj[i]))
        return retList

class bitField(field):
    def __init__(self, in_field, bitMask=0, bitShift=0):
        super().__init__(in_field.start, in_field.length)
        self.mask = bitMask
        self.in_field = in_field
        self.shift = bitShift
    def getValue(self, payload):
        objVal = self.in_field.getValue(payload)
        return (objVal & self.mask) >> self.shift

class calculatedField(field):
    def __init__(self):
        pass
    def getValue(self):
        pass

class posGroup(field):
    def __init__(self, start=0, postFilter=noFilter):
        super().__init__(start=start, length=12, postFilter=postFilter)
        self.structString = '<fff'

    def getValue(self, payload):
        retDict = {}
        obj = struct.unpack_from(self.structString, payload, self.start)
        retDict['X'] = obj[0]
        retDict['Z'] = obj[1]
        retDict['Y'] = obj[2]
        return retDict

class statGroup(field):
    def __init__(self, start=0, skip=0, count=7):
        super().__init__(start, count)
        self.count = count
        self.skip = skip
        self.structString = '<' + str(count) + 'H'

    def getValue(self, payload):
        structObj= struct.unpack_from(self.structString, payload, self.start)
        retList = []
        for i in range(self.count):
            retList.append((ffxi_supportClasses.stats[i + self.skip], structObj[i]))
        return retList

class equipSlotGroup(field):
    def __init__(self, start=0, skip=0, count=16):
        super().__init__(start, count)
        self.count = count
        self.skip = skip
        self.structString = '<' + 'BBBBHH' * self.count

    def getValue(self, payload):
        structObj = struct.unpack_from(self.structString, payload, self.start)
        retList = []
        for i in range(self.count):
            retList.append( (ffxi_supportClasses.equipSlot, structObj[i*6:(i*6)+6] ))

#types.lockstyleset = L{
#    {ctype='unsigned char',     label='Inventory Index'},                       -- 00
#    {ctype='unsigned char',     label='Equipment Slot',     fn=slot},           -- 01
#    {ctype='unsigned char',     label='Bag',                fn=bag},            -- 02
#    {ctype='unsigned char',     label='_unknown2',          const=0x00},        -- 03
#    {ctype='unsigned short',    label='Item',               fn=item},           -- 04
#    {ctype='unsigned short',    label='_unknown3',          const=0x0000},      -- 06


class shopItem(field):
    def __init__(self, start=0, skip=0, count=-1):
        super().__init__(start, count)
        self.count = count
        self.skip = skip
        self.structString = '<LHHHH'

    def getValue(self, payload):
        return None

#types.shop_item = L{
#    {ctype='unsigned int',      label='Price',              fn=gil},            -- 00
#    {ctype='unsigned short',    label='Item',               fn=item},           -- 04
#    {ctype='unsigned short',    label='Shop Slot'},                             -- 08
#    {ctype='unsigned short',    label='Craft Skill'},                           -- 0A Zero on normal shops, has values that correlate to res\skills.
#    {ctype='unsigned short',    label='Craft Rank'},                            -- 0C Correlates to Rank able to purchase product from GuildNPC  
#}

class blacklistEntry(field):
    def __init__(self, start=0, skip=0, count=-1):
        super().__init__(start, count)
        self.count = count
        self.skip = skip
        self.structString = 'L16s'

    def getValue(self, payload):
        pass

#types.blacklist_entry = L{
#    {ctype='unsigned int',      label='ID'},                                    -- 00
#    {ctype='char[16]',          label='Name'},                                  -- 04
#}

class conditional(field):
    def __init__(self, condition, field):
        self.field = field
        self.condition = condition
    def getValue(self, payload):
        if self.condition(payload):
            return self.field.getValue(payload)
        else:
            return None

class uint8(field):
    def __init__(self, start=0, postFilter=noFilter):
        super().__init__(start, 1, postFilter=postFilter)
        self.structString = 'B'

class int8(field):
    def __init__(self, start=0, postFilter=noFilter):
        super().__init__(start, 1, postFilter=postFilter)
        self.structString = 'B'
 
class ushort(field):
    def __init__(self, start=0, postFilter=noFilter):
        super().__init__(start,2, postFilter=postFilter)
        self.structString = '<H'

class short(field):
    def __init__(self, start=0, postFilter=noFilter):
        super().__init__(start,2, postFilter=postFilter)
        self.structString = '<h'

class float(field):
    def __init__(self, start=0, postFilter=noFilter):
        super().__init__(start, 4, postFilter=postFilter)
        self.structString = '<f'

class uFloat(field):
    def __init__(self, start=0, postFilter=noFilter):
        super().__init__(start, 4, postFilter=postFilter)
        self.structString = '<F'

class long(field):
    def __init__(self, start=0, postFilter=noFilter):
        super().__init__(start, 4, postFilter=postFilter)
        self.structString = '<l'

class ulong(field):
    def __init__(self, start=0, postFilter=noFilter):
        super().__init__(start, 4, postFilter=noFilter)
        self.structString = '<L'

class double(field):
    def __init__(self, start=0, postFilter=noFilter):
        super().__init__(start, 8, postFilter=postFilter)
        self.structString = '<q'

class uDouble(field):
    def __init__(self, start=0, postFilter=noFilter):
        super().__init__(start, 8, postFilter=postFilter)
        self.structString = '<Q'




class template(object):

    pktTypeMask = 0x01ff
    pktSizeMask = 0x0fe
    def iParse(pktPayload):
        packetType = struct.unpack_from('<H', pktPayload, 0)[0] & template.pktTypeMask
        packetSize = (struct.unpack_from('<B', pktPayload, 1)[0] & template.pktSizeMask) * 2
        packetSequence = struct.unpack_from('<H', pktPayload, 2)[0]
        return (packetType, packetSize, packetSequence)

    def __init__(self, size, typeId, direction=1  ,src='', sstruct='', srcFile='', notes=''):
        self.name = type(self).__name__
        self.size = size
        self.sstruct = sstruct
        self.src = src
        self.srcFile = srcFile
        self.notes = notes
        self.typeId = typeId
        self.direction = direction
        self.fields = {} #name: field
        self.fields['PacketType'] = ushort(0x0)
        self.fields['PacketSize'] = uint8(1)
        self.fields['PacketType'].getValue = lambda payload: struct.unpack_from('<H', payload)[0] & template.pktTypeMask
        self.fields['PacketSize'].getValue = lambda payload: ((struct.unpack_from('<B', payload, 1)[0] & template.pktSizeMask) *2)
        self.fields['PacketSequence'] = ushort(0x02)

        if self.sstruct == '':
            self.genStruct()

    

    def getFields(self, payload):
        retDict = {}
        for k,v in self.fields.items():
            val = v.getValue(payload)
            if val is not None:
                retDict[k] = v.getValue(payload)
        return retDict


    def makeTemplate(self):
        rTemplate = ffxi_sql.packetTemplates()
        rTemplate.name = self.name
        rTemplate.notes = self.notes
        rTemplate.size = self.size
        rTemplate.struct = self.sstruct
        rTemplate.src = self.src
        rTemplate.typeId = self.typeId

    def genObjects(self, buffer):
        if self.sstruct == '':
            return None
        else:
            pass

    def testPayload(self, buffer):
        testLen = struct.calcsize(self.sstruct)
        if len(buffer) != testLen:
            return False
        else:
            return True

    def __readSources(self):
        return ''

    def genStruct(self):
        return ''

    def genNotes(self):
        return self.notes

    def rawReadSource(self):
        if self.srcFile != '' or self.srcFile is None:
            if os.path.exists(self.srcFile):
                fileData = open(self.srcFile,'rb')
                retString = fileData.read().decode('utf-8')
                fileData.close()
                return retString
            else:
                return '%s File not found' % self.srcFile
        else:
            return ''

    def __repr__(self):
        return 'typeId: %s Size: %s class name: %s' % (self.typeId, self.size, type(self).__name__)

    def getHex(self, payload):
        return hexdump(payload)

#windower lua based outbound

class oClientConnect(template):
    def __init__(self):
        super().__init__(0,0x0a,notes='(unencrypted/uncompressed) First packet sent when connecting to new zone.')

class oZoneIn1(template):
    def __init__(self):
        super().__init__(0,0x0c, notes='Likely triggers certain packets to be sent from the server.')
        self.fields['_unknown1'] = ushort(0x04)
        self.fields['_unknown2'] = ushort(0x06)

class oClientLeave(template):
    def __init__(self):
        super().__init__(0,0x0d,notes='Last packet sent from client before it leaves the zone.')
        self.fields['_unknown1'] = uint8(0x04)
        self.fields['_unknown2'] = uint8(0x05)
        self.fields['_unknown3'] = uint8(0x06)
        self.fields['_unknown4'] = uint8(0x07)



class oZoneIn2(template):
    def __init__(self):
        super().__init__(0,0x0f,notes='Likely triggers certain packets to be sent from the server.')
        self.fields['_unknown1'] = field(0x04, 32)

class oZoneIn3(template):
    def __init__(self):
        super().__init__(0,0x11, notes='Likely triggers certain packets to be sent from the server.')
        self.fields['_unknown1'] = long(0x04)

class oStandardClient(template):
    def __init__(self):
        super().__init__(0,0x15, notes='Packet contains data that is sent almost every time (i.e your character\'s position).')
        self.fields['X'] = float(0x04)
        self.fields['Z'] = float(0x08)
        self.fields['Y'] = float(0x0c)
        self.fields['_junk1'] = ushort(0x10)
        self.fields['RunCount'] = ushort(0x12)
        self.fields['Rotation'] = uint8(0x14)
        self.fields['_flags1'] = uint8(0x15) #Bit 0x04 indicates that maintenance mode is activated
        self.fields['TargetIdx'] = ushort(0x16)
        self.fields['Timestamp'] = ulong(0x18)
        self.fields['_unkonwn3'] = ulong(0x1c)

class oUpdateRequest(template):
    def __init__(self):
        super().__init__(0,0x16, notes='Packet that requests a PC/NPC update packet.')
        self.fields['TargetIdx'] = ushort(0x04)
        self.fields['_junk1'] = ushort(0x06)
        
class oNPCRaceError(template):
    def __init__(self):
        super().__init__(0,0x17, notes='Packet sent in response to impossible incoming NPC packets (like trying to put equipment on a race 0 monster).')
        self.fields['NPCIdx'] = ushort(0x04)
        self.fields['_unkonw1'] = ushort(0x06)
        self.fields['NPC_ID'] = ulong(0x08)
        self.fields['_unknown2'] = field(0x0c, 6)
        self.fields['ReportedNPCType'] = uint8(0x12)
        self.fields['_unkonw3'] = uint8(0x13)

class oAction(template):
    def __init__(self):
        super().__init__(0,0x1a,notes='An action being done on a target (i.e. an attack or spell).')
        self.fields['TargetId'] = ulong(0x04)
        self.fields['TargetIdx'] = ushort(0x08)
        self.fields['Category'] = ushort(0x0a)
        self.fields['Param'] = ushort(0x0c)
        self.fields['_unkonw1'] = ushort(0x0e)
        self.fields['X'] = float(0x10)
        self.fields['Z'] = float(0x14)
        self.fields['Y'] = float(0x18)

class oVolunteer(template):
    def __init__(self):
        super().__init__(0,0x1e, notes='Sent in response to a /volunteer command.')

class oDropItem(template):
    def __init__(self):
        super().__init__(0,0x28,notes='Drops an item.')
        self.fields['Count'] = ulong(0x04)
        self.fields['Bag'] = uint8(0x08, postFilter=lambda val: ffxi_supportClasses.bags[val])
        self.fields['InventoryIdx'] = uint8(0x09)
        self.fields['_junk1'] = ushort(0x0a)

class oMoveItem(template):
    def __init__(self):
        super().__init__(0,0x29,notes='Move item from one inventory to another.')
        self.fields['Count'] = ulong(0x04)
        self.fields['Bag'] = uint8(0x08)
        self.fields['TargetBag'] = uint8(0x09)
        self.fields['CurrentIdx'] = uint8(0x0a)
        self.fields['TargetIdx'] = uint8(0x0b)

class oTranslateRequest(template):
    def __init__(self):
        super().__init__(0, 0x2b, notes='Request that a phrase be translated.')
        self.fields['StartingLanguage'] = uint8(0x04)
        self.fields['EndingLanguage'] = uint8(0x05)
        self.fields['_unknown1'] = ushort(0x06)
        self.fields['Phrase'] = field(0x08, 64, postFilter=nullTerminatedString)

class oTradeRequest(template):
    def __init__(self):
        super().__init__(0,0x32,notes='This is sent when you offer to trade somebody.')
        self.fields['Target'] = ulong(0x04)
        self.fields['TargetIdx'] = ushort(0x08)
        self.fields['_junk1'] = field(0x0a,2)

class oTradeConfirm(template):
    def __init__(self):
        super().__init__(0,0x33,notes='This packet allows you to accept or cancel a trade.')
        self.fields['Type'] = ulong(0x04)
        self.fields['TradeCount'] = ulong(0x08) 

class oTradeOffer(template):
    def __init__(self):
        super().__init__(0,0x34,notes='Sends the item you want to trade to the server.')
        self.fields['Count'] = ulong(0x04)
        self.fields['Item'] = ushort(0x08)
        self.fields['InventoryIdx'] = uint8(0x0a)
        self.fields['Slot'] = uint8(0x0b)

class oMenuItem(template):
    def __init__(self):
        super().__init__(0,0x36, notes='Use an item from the item menu.')

class oUseItem(template):
    def __init__(self):
        super().__init__(0,0x37,notes='Use an item.')

class oSortItem(template):
    def __init__(self):
        super().__init__(0,0x3a, notes='Stacks the items in your inventory. Sent when hitting "Sort" in the menu.')
        self.fields['Bag'] = uint8(0x04)
        self.fields['_unkonwn1'] = uint8(0x05)
        self.fields['_unknown2'] = ushort(0x06)

class oBlacklistCommand(template):
    def __init__(self):
        super().__init__(0,0x3d, notes='Sent in response to /blacklist add or /blacklist delete.')
        self.fields['_unknown1'] = ulong(0x04)
        self.fields['Name'] = field(0x08, 16, postFilter=nullTerminatedString)
        self.fields['AddRemove'] = uint8(0x18)
        self.fields['_unknown2'] = field(0x19,3)

class oLotItem(template):
    def __init__(self):
        super().__init__(0,0x41, notes='Lotting an item in the treasure pool.')
        self.fields['Slot'] = ulong(0x04)

class oPassItem(template):
    def __init__(self):
        super().__init__(0,0x42, notes='Passing an item in the treasure pool.')
        self.fields['Slot'] = ulong(0x04)

class oServMes(template):
    def __init__(self):
        super().__init__(0,0x4b, notes='Requests the server message (/servmes).')
        self.fields['_unknown1'] = uint8(0x04)
        self.fields['_unknown2'] = uint8(0x05)
        self.fields['_unknown3'] =  uint8(0x06)
        self.fields['_unknown4'] = uint8(0x07)
        self.fields['_unknown5'] = field(0x08, 12)
        self.fields['_unknown6'] = ulong(0x14)

class oDeliveryBox(template):
    def __init__(self):
        super().__init__(0,0x4d, notes='Used to manipulate the delivery box.')
        self.fields['Type'] = uint8(0x04)
        self.fields['_unknown1'] = uint8(0x05)
        self.fields['Slot' ] = uint8(0x06)
        self.fields['_unknown2'] = field(0x07, 5)
        self.fields['_unknown3'] = field(0x0c, 20)

class oAuction(template):
    def __init__(self):
        super().__init__(0,0x4e, notes='Used to bid on an Auction House item.')

class oEquip(template):
    def __init__(self):
        super().__init__(0,0x50,notes='This command is used to equip your character.')
        self.fields['ItemIdx'] = uint8(0x04)
        self.fields['EquipSlot'] = uint8(0x05)
        self.fields['Bag' ] = uint8(0x06)
        self.fields['_junk1'] = uint8(0x07)

class oEquipSet(template):
    def __init__(self):
        super().__init__(0,0x51, notes='This packet is sent when using /equipset.')

class oEquipSetBuild(template):
    def __init__(self):
        super().__init__(0,0x52,notes='This packet is sent when building an equipset.')
        self.fields['NewEquipSlot'] = uint8(0x04)
        self.fields['_unknown1'] = field(0x05,3)
        self.notes = self.notes + '\nMore to add, handle complex types'

class oLockstyleEet(template):
    def __init__(self):
        super().__init__(0,0x53, notes='This packet is sent when locking to an equipset.')
        self.fields['Count'] = uint8(0x04)
        self.fields['Type'] = uint8(0x05)
        self.fields['_unknown1'] = ushort(0x06)
        self.fields['EquipSetItems'] = equipSlotGroup(0x04)


class oEndSynth(template):
    def __init__(self):
        super().__init__(0,0x59,notes='This packet is sent to end a synth.')
        self.fields['_unknown1'] = ulong(0x04)
        self.fields['_junk1'] = field(0x08,8)

class oConquest(template):
    def __init__(self):
        super().__init__(0,0x5a, notes='This command asks the server for data pertaining to conquest/besieged status.')

class oDialogChoice(template):
    def __init__(self):
        super().__init__(0,0x5b,notes='Chooses a dialog option.')
        self.fields['Target'] = ulong(0x04)
        self.fields['OptionIdx'] = ushort(0x08)
        self.fields['_unknown1'] = ushort(0x0a)
        self.fields['TargetIdx'] = ushort(0x0c)
        self.fields['AutomatedMessage'] = uint8(0x0e)
        self.fields['_unknown2'] = uint8(0x0f)
        self.fields['Zone'] = ushort(0x10)
        self.fields['MenuId'] = ushort(0x12)

class oWarpRequest(template):
    def __init__(self):
        super().__init__(0,0x5c, notes='Request a warp. Used by teleporters and the like.')
        self.fields['X'] = float(0x04)
        self.fields['Z'] = float(0x08)
        self.fields['Y'] = float(0x0c)
        self.fields['TargetId'] = ulong(0x10)
        self.fields['_unknown1'] = ulong(0x14)
        self.fields['Zone'] = ushort(0x18)
        self.fields['MenuId'] = ushort(0x1a)
        self.fields['TargetIdx'] = ushort(0x1c)
        self.fields['_unknown3'] = ushort(0x1e)

class oEmote(template):
    def __init__(self):
        super().__init__(0,0x5d, notes='This command is used in emotes.')
        self.fields['TargetId'] = ulong(0x04)
        self.fields['TargetIdx'] = ushort(0x08)
        self.fields['Emote'] = uint8(0x0a)
        self.fields['Type'] = uint8(0x0b)
        self.fields['_unknown1'] = ulong(0x0c)

class oRequestZone(template):
    def __init__(self):
        super().__init__(0,0x5e, notes='Request from the client to zone.')
        self.fields['ZoneLine'] = ulong(0x04)
        self.fields['_unknown1'] = field(0x08, 12)

class oEquipmentScreen(template):
    def __init__(self):
        super().__init__(0,0x61, notes='This command is used when you open your equipment screen.')

class oDiggingFinished(template):
    def __init__(self):
        super().__init__(0,0x63, notes='This packet is sent when the chocobo digging animation is finished.')
        self.fields['PlayerId'] = ulong(0x04)
        self.fields['_unknown1'] = ulong(0x08)
        self.fields['PlayerIdx'] = ushort(0x0c)
        self.fields['Action?'] = uint8(0x0e)
        self.fields['_junk1'] = uint8(0x0f)

class oNewKIExamination(template):
    def __init__(self):
        super().__init__(0,0x64, notes='Sent when you examine a key item with a "new" flag on it.')
        self.fields['PlayerId'] = ulong(0x04)
        self.fields['Flags'] = field(0x08,40)
        self.fields['_unknown1'] = ulong(0x48)

class oPartyInvite(template):
    def __init__(self):
        super().__init__(0,0x6e, notes='Sent when inviting another player to either party or alliance.')
        self.fields['TargetId'] = ulong(0x04)
        self.fields['TargetIdx'] = ushort(0x08)
        self.fields['Alliance'] = uint8(0x0a)
        self.fields['_const1'] = uint8(0x0b)

class oPartyLeave(template):
    def __init__(self):
        super().__init__(0,0x6f, notes='Sent when leaving the party or alliance.')
        self.fields['Alliance'] = uint8(0x04)
        self.fields['_junk1'] = field(0x05,3)

class oPartyBreakup(template):
    def __init__(self):
        super().__init__(0,0x70, notes='Sent when disbanding the entire party or alliance.')
        self.fields['Alliance'] = uint8(0x04)
        self.fields['_junk1'] = field(0x05, 3)

class oKick(template):
    def __init__(self):
        super().__init__(0,0x71, notes='Sent when you kick someone from linkshell or party.')
        self.fields['_unknown1'] = field(0x04, 6)
        self.fields['KickType'] = uint8(0x0a)
        self.fields['_unknown2'] = uint8(0x0b)
        self.fields['MemberName'] = field(0x0c, 16)

class oPartyResponse(template):
    def __init__(self):
        super().__init__(0,0x74, notes='Sent when responding to a party or alliance invite.')
        self.fields['Join'] = uint8(0x04)
        self.fields['_junk1'] = field(0x05,3)

class oChangePermissions(template):
    def __init__(self):
        super().__init__(0,0x77, notes='Sent when giving party or alliance leader to another player or elevating/decreasing linkshell permissions.')
        self.fields['TargetName'] = field(0x04, 16, postFilter=nullTerminatedString)
        self.fields['PartyType'] = uint8(0x14)
        self.fields['Permissions'] = uint8(0x15)
        self.fields['_unknown'] = ushort(0x16)

class oPartyListRequest(template):
    def __init__(self):
        super().__init__(0,0x78, notes='Sent when giving party or alliance leader to another player or elevating/decreasing linkshell permissions.')

class oGuildNPCBuy(template):
    def __init__(self):
        super().__init__(0, 0x82, notes='Guild NPC Buy Sent when buying an item from a guild NPC')
        self.fields['_missing'] = ulong(0x04)
        self.fields['Item'] = ushort(0x08)
        self.fields['_unknown1'] = uint8(0x0a)
        self.fields['Count'] = uint8(0x0b)

class oNPCBuyItem(template):
    def __init__(self):
        super().__init__(0,0x83, notes='Buy an item from a generic NPC.')
        self.fields['Count'] = ulong(0x04)
        self.fields['_unknown2'] = ushort(0x08)
        self.fields['ShopSlot'] = uint8(0x0a)
        self.fields['_unknown3'] = uint8(0x0b)
        self.fields['_unknown4'] = ulong(0x0c)

class oAppraise(template):
    def __init__(self):
        super().__init__(0,0x84, notes='Ask server for selling price.')
        self.fields['Count'] = ulong(0x04)
        self.fields['Item'] = ushort(0x08)
        self.fields['InventoryIdx'] = uint8(0x0a)
        self.fields['_unknown3'] = uint8(0x0b)
        self.notes = self.notes + '\nNeeds additional review'

class oSellConfirm(template):
    def __init__(self):
        super().__init__(0,0x85, notes='Sell an item from your inventory.')
        self.fields['_unknown1'] = ulong(0x04)

class oSynth (template):
    def __init__(self):
        super().__init__(0,0x96, notes='Packet sent containing all data of an attempted synth.')
        self.fields['_unknown1'] = uint8(0x04) # crystal
        self.fields['_unknown2'] = uint8(0x05)
        self.fields['Crystal'] = ushort(0x06)
        self.fields['CrystalIdx'] = uint8(0x08)
        self.fields['IngredientCount'] = uint8(0x09)
        self.fields['Ingredient1'] = ushort(0x0a)
        self.fields['Ingredient2'] = ushort(0x0c)
        self.fields['Ingredient3'] = ushort(0x0e)
        self.fields['Ingredient4'] = ushort(0x10)
        self.fields['Ingredient5'] = ushort(0x12)
        self.fields['Ingredient6'] = ushort(0x14)
        self.fields['Ingredient7'] = ushort(0x16)
        self.fields['Ingredient8'] = ushort(0x18)
        self.fields['IngredientIdx1'] = uint8(0x1a)
        self.fields['IngredientIdx2'] = uint8(0x1b)
        self.fields['IngredientIdx3'] = uint8(0x1c)
        self.fields['IngredientIdx4'] = uint8(0x1d)
        self.fields['IngredientIdx5'] = uint8(0x1e)
        self.fields['IngredientIdx6'] = uint8(0x1f)
        self.fields['IngredientIdx7'] = uint8(0x20)
        self.fields['IngredientIdx8'] = uint8(0x21)
        self.fields['_junk1'] = ushort(0x22)

class oNominate(template):
    def __init__(self):
        super().__init__(0,0xa0, notes='Sent in response to a /nominate command.')

class oVote(template):
    def __init__(self):
        super().__init__(0,0xa1, notes='Sent in response to a /vote command.')

class oRandom(template):
    def __init__(self):
        super().__init__(0,0xa2, notes='Sent in response to a /random command.')

class oGuildBuyItem(template):
    def __init__(self):
        super().__init__(0,0xa4, notes='Buy an item from a guild.')
###
class oGetGuildInvList(template):
    def __init__(self):
        super().__init__(0,0xab, notes='Gets the offerings of the guild. triggers 0x83 inbound\nSize 4b, (empty payload)')


class oGildSellItem(template):
    def __init__(self):
        super().__init__(0,0xac, notes='Sell an item to the guild.')
        self.fields['Item'] = ushort(0x04)
        self.fields['_unknown1'] = uint8(0x06)
        self.fields['Count'] = uint8(0x07)

class oGetGuildSaleList(template):
    def __init__(self):
        super().__init__(0,0xad, notes='Gets the list of things the guild will buy. Triggers 0x85 inbound\nSize 4b, (empty payload)')


class oSpeech(template):
    def __init__(self):
        super().__init__(0,0xb5,notes='Packet contains normal speech.')
        self.fields['Mode'] = uint8(0x04)
        self.fields['GMFlag'] = uint8(0x05)
        self.fields['Message'] = varString(0x06)


class oTell(template):
    def __init__(self):
        super().__init__(0,0xb6, notes='/tell\'s sent from client.')
        self.fields['_unknown1'] = uint8(0x04)
        self.fields['TargetName'] = string(0x05,15, nullTerminatedString)
        self.fields['Message'] = varString(0x14)

class oMeritPointIncrease(template):
    def __init__(self):
        super().__init__(0,0xbe, notes='Sent when you increase a merit point ability.')
        self.fields['_unknown1'] = uint8(0x04)
        self.fields['Flag'] = uint8(0x05)
        self.fields['MeritPoint'] = ushort(0x06)
        self.fields['_unknown2'] = ulong(0x08)

class oJobPointIncrease(template):
    def __init__(self):
        super().__init__(0,0xbf, notes='Sent when you increase a job point ability.')
        self.fields['Type'] = bitField(ushort(0x04), 63488)
        self.fields['Job'] = bitField(ushort(0x04), 2047)
        self.fields['_junk1'] = ushort(0x06)


class oJobPointMenu(template):
    def __init__(self):
        super().__init__(0,0xc0, notes='Sent when you open the Job Point menu and triggers Job Point Information packets. -- empty packet')

class oMakeLinkshell(template):
    def __init__(self):
        super().__init__(0,0xc3, notes='Sent in response to the /makelinkshell command.')

class oEquipLinkshell(template):
    def __init__(self):
        super().__init__(0,0xc4, notes='Sent to equip a linkshell.')

class oOpenMog(template):
    def __init__(self):
        super().__init__(0,0xcb, notes='Sent when opening or closing your mog house.')

class oPartyMarkerRequest(template):
    def __init__(self):
        super().__init__(0,0xd2, notes='Requests map markers for your party.')

class oGMCall(template):
    def __init__(self):
        super().__init__(0,0xd3, notes='Places a call to the GM queue.')

class oHelpDeskMenu(template):
    def __init__(self):
        super().__init__(0,0xd4, notes='Opens the Help Desk submenu.')

class oTypeBitmask(template):
    def __init__(self):
        super().__init__(0,0xdc, notes='This command is sent when change your party-seek or /anon status.')

class oCheck(template):
    def __init__(self):
        super().__init__(0,0xdd, notes='Used to check other players.')

class oSetBazaarMessage(template):
    def __init__(self):
        super().__init__(0,0xde, notes='Sets your bazaar message.')

class oSearchComment(template):
    def __init__(self):
        super().__init__(0,0xe0, notes='Sets your search comment.')

class oGetLSMes(template):
    def __init__(self):
        super().__init__(0,0xe1, notes='Requests the current linkshell message.')

class oSetLSMes(template):
    def __init__(self):
        super().__init__(0,0xe2, notes='Sets the current linkshell message.')

class oSit(template):
    def __init__(self):
        super().__init__(0,0xea, notes='A request to sit or stand is sent to the server.')

class oLogout(template):
    def __init__(self):
        super().__init__(0,0xe7, notes='A request to logout of the server.')

class oToggleHeal(template):
    def __init__(self):
        super().__init__(0,0xe8, notes='This command is used to both heal and cancel healing.')

class oCancel(template):
    def __init__(self):
        super().__init__(0,0xf1, notes='Sent when canceling a buff.')

class oDeclareSUbregion(template):
    def __init__(self):
        super().__init__(0,0xf2, notes='Sent when moving to a new subregion of a zone (for instance, a different combination of open doors).')

class oWidescan(template):
    def __init__(self):
        super().__init__(0,0xf4, notes='This command asks the server for a widescan.')

class oWidescanTrack(template):
    def __init__(self):
        super().__init__(0,0xf5, notes='Sent when you choose to track something on widescan.')

class oWidescanCancel(template):
    def __init__(self):
        super().__init__(0,0xf6, notes='Sent when you choose to stop track something on widescan.')

class oPlaceFurniture(template):
    def __init__(self):
        super().__init__(0,0xfa, notes='Sends new position for your furniture.')

class oRemoveFurniture(template):
    def __init__(self):
        super().__init__(0,0xfb, notes='Informs the server you have removed some furniture.')

class oPlantFlowerpot(template):
    def __init__(self):
        super().__init__(0,0xfc, notes='Plants a seed in a flowerpot.')

class oExamineFlowerpot(template):
    def __init__(self):
        super().__init__(0,0xfd, notes='Sent when you examine a flowerpot.')

class oUprootFlowerpot(template):
    def __init__(self):
        super().__init__(0,0xfe, notes='Uproots a flowerpot.')

class oJobChange(template):
    def __init__(self):
        super().__init__(0,0x100, notes='Sent when initiating a job change.')

class oUntraditionalEquip(template):
    def __init__(self):
        super().__init__(0,0x102, notes='Sent when equipping a pseudo-item like an Automaton Attachment, Instinct, or Blue Magic Spell.Sent when equipping a pseudo-item like an Automaton Attachment, Instinct, or Blue Magic Spell.')

class oLeaveBazaar(template):
    def __init__(self):
        super().__init__(0,0x104, notes='Sent when client leaves a bazaar.')

class oViewBazaar(template):
    def __init__(self):
        super().__init__(0,0x105, notes='Sent when viewing somebody\'s bazaar.')

class oBuyBazaarItem(template):
    def __init__(self):
        super().__init__(0,0x106, notes='Buy an item from somebody\'s bazaar.')

class oCloseBazaar(template):
    def __init__(self):
        super().__init__(0,0x109, notes='Sent after closing your bazaar window.')

class oSetPrice(template):
    def __init__(self):
        super().__init__(0,0x10a, notes='Set the price on a bazaar item.')

class oOpenBazaar(template):
    def __init__(self):
        super().__init__(0,0x10b, notes='Sent when opening your bazaar window to set prices.')

class oStartRoEQuest(template):
    def __init__(self):
        super().__init__(0,0x10c, notes='Sent to undertake a Records of Eminence Quest.')

class oCancelRoEQuest(template):
    def __init__(self):
        super().__init__(0,0x10d, notes='Sent to cancel a Records of Eminence Quest.')

class oAcceptRoEReward(template):
    def __init__(self):
        super().__init__(0,0x10e, notes='Accept an RoE qust reward that was not given automatically due to inventory restrictions.')

class oCurrencyMenu(template):
    def __init__(self):
        super().__init__(0,0x10f, notes='Requests currency information for the menu.')

class oFishingAction(template):
    def __init__(self):
        super().__init__(0,0x110, notes='Sent when casting, releasing a fish, catching a fish, and putting away your fishing rod.')

class oLockstyle(template):
    def __init__(self):
        super().__init__(0,0x111, notes='Sent when using the lockstyle command to lock or unlock.')

class oRoELogRequest(template):
    def __init__(self):
        super().__init__(0,0x112, notes='Sent when zoning. Requests the ROE quest log.')

class oHPMapTrigger(template):
    def __init__(self):
        super().__init__(0,0x114, notes='Sent when entering a homepoint list for a zone to trigger maps to appear.')

class oCurrencyMenu2(template):
    def __init__(self):
        super().__init__(0,0x115, notes='Requests currency 2 information for the menu.')

class oUnityMenu(template):
    def __init__(self):
        super().__init__(0,0x116, notes='Sent when opening the Status/Unity menu.')

class oUnityRankingMenu(template):
    def __init__(self):
        super().__init__(0,0x117, notes='Sent when opening the Status/Unity/Unity Ranking menu.')

class oUnityChatStatus(template):
    def __init__(self):
        super().__init__(0,0x118, notes='Sent when changing unity chat status.')

#windower lua incoming packets
class iStandardMessage(template):
    def __init__(self):
        super().__init__(0,0x09, direction=0, notes='A standardized message send from FFXI.')

class iZoneIn(template): ### packet array entries sent to initialize inventory array client side after zoning-- followed by a finished inventory packet 0x1d, updates are then processed transactionally via imodifiy & iitemassign(for status)
    def __init__(self):
        super().__init__(0,0x0a, direction=0, notes='Info about character and zone around it.')
        self.fields['PlayerId'] = ulong(4)
        self.fields['PlayerIdx'] = ushort(8)
        self.fields['_padding'] = uint8(0x0a)
        self.fields['Heading'] = uint8(0x0b)
        self.fields['Pos'] = posGroup(0x0c)
        self.fields['runCount'] = ushort(0x18)
        self.fields['targetIdx'] = ushort(0x1a)
        self.fields['movementSpeed'] = uint8(0x1c)
        self.fields['AnimationSpeed'] = uint8(0x1d)
        self.fields['hpp'] = uint8(0x1e)
        self.fields['status'] = uint8(0x1f)
        self.fields['_unknown1'] = field(0x20,16)
        self.fields['zoneid'] = ushort(0x30, lambda val: ffxi_supportClasses.zones[val])
        self.fields['_unknown2'] = field(0x32,6)
        self.fields['timstamp1'] = ulong(0x38)
        self.fields['timestamp2'] = ulong(0x3c)
        self.fields['_unknown3'] = ushort(0x40)
        self.fields['_dupZoneId'] = ushort(0x42)
        self.fields['face'] = uint8(0x44)
        self.fields['race'] = uint8(0x45)
        self.fields['head'] = ushort(0x46)
        self.fields['body'] = ushort(0x48)
        self.fields['hands'] = ushort(0x4a)
        self.fields['legs'] = ushort(0x4c)
        self.fields['feet'] = ushort(0x4e)
        self.fields['main'] = ushort(0x50)
        self.fields['sub'] = ushort(0x52)
        self.fields['ranged'] = ushort(0x54)
        self.fields['dayMusic'] = ushort(0x56)
        self.fields['nightMusic'] = ushort(0x58)
        self.fields['soloCombatMusic'] = ushort(0x5a)
        self.fields['partyCombatMusic'] = ushort(0x5c)
        self.fields['_unknown4'] = field(0x5e,4)
        self.fields['menuZone'] = ushort(0x62)
        self.fields['menuId'] = ushort(0x64)
        self.fields['_unknown5'] = ushort(0x66)
        self.fields['weather'] = ushort(0x68)
        self.fields['_unknown6'] = ushort(0x6a)
        self.fields['_unknown7'] = field(0x6c, 24)
        self.fields['PlayerName'] = field(0x84, 16, postFilter=nullTerminatedString)
        self.fields['_unknown8'] = field(0x94, 12)
        self.fields['abyssea timestamp'] = ulong(0xa0)
        self.fields['_unkonwn9'] = ulong(0xa4)
        self.fields['_unknown10'] = field(0xa8, 2)
        self.fields['zoneModel']  = ushort(0xaa)
        self.fields['_unknown11'] = field(0xac, 8)
        self.fields['mainJob'] = uint8(0xb4)
        self.fields['_unknown12'] = uint8(0xb5)
        self.fields['_unkonwn13'] = uint8(0xb6)
        self.fields['subJob'] = uint8(0xb7)
        self.fields['_unkonwn14'] = ulong(0xb8)
        self.fields['Jobs'] = jobGroup(0xbc,skip=0, count=16)
        self.fields['BaseStats'] = statGroup(0xcc)
        self.fields['BonusStats'] = statGroup(0xda)
        self.fields['maxHP'] = ulong(0xe8)
        self.fields['maxMP'] = ulong(0xec)
        self.fields['_unknown15'] = field(0xf0,20)
        

class iZoneOut(template):
    def __init__(self):
        super().__init__(0,0x0b, direction=0, notes='Packet contains IP and port of next zone to connect to.')
        self.fields['Type'] = ulong(0x04)
        self.fields['IP'] = ulong(0x08)
        self.fields['Port'] = ulong(0x0c)


class iPCUpdate(template):
    def __init__(self):
        super().__init__(0,0x0d, direction=0, notes='Packet contains info about another PC (i.e. coordinates).')
        b20Flags = { 0x01: 'None', 0x02:'Deletes everyone', 0x04:'Deletes Everyone', 0x08:'None', 0x10:'None', 0x20:'None', 0x40:'None', 0x80:'None'}
        b21Flags = { 0x01:'None', 0x02:'None', 0x04:'None', 0x08:'LFG', 0x10:'Anon', 0x20:'Orange', 0x40:'Away', 0x80:'None'}
        b22Flags = { 0x01:'Pol icon', 0x02:'None', 0x04:'DCing', 0x08:'Untargetable', 0x10:'No linkshell', 0x20:'No linkshell', 0x40:'No linkshell', 0x80:'No linkshell' }
        b23Flags = { 0x01:'Trial account',0x02:'Trial account', 0x04:'GM Mode', 0x08:'None',0x10:'None', 0x20:'Invisible name' }
#    -- Byte 0x23:
#    -- 01 = Trial Account
#    -- 02 = Trial Account
#    -- 04 = GM Mode
#    -- 08 = None
#    -- 16 = None
#    -- 32 = Invisible models
#    -- 64 = None
#    -- 128 = Bazaar

#    {ctype='unsigned int',      label='Player',             fn=id},             -- 04
#    {ctype='unsigned short',    label='Index',              fn=index},          -- 08
#    {ctype='boolbit',           label='Update Position'},                       -- 0A:0 Position, Rotation, Target, Speed  
#    {ctype='boolbit',           label='Update Status'},                         -- 1A:1 Not used for 0x00D
#    {ctype='boolbit',           label='Update Vitals'},                         -- 0A:2 HP%, Status, Flags, LS color, "Face Flags"
#    {ctype='boolbit',           label='Update Name'},                           -- 0A:3 Name
#    {ctype='boolbit',           label='Update Model'},                          -- 0A:4 Race, Face, Gear models
#    {ctype='boolbit',           label='Despawn'},                               -- 0A:5 Only set if player runs out of range or zones
#    {ctype='boolbit',           label='_unknown1'},                             -- 0A:6
#    {ctype='boolbit',           label='_unknown2'},                             -- 0A:6
#    {ctype='unsigned char',     label='Heading',            fn=dir},            -- 0B
#    {ctype='float',             label='X'},                                     -- 0C
#    {ctype='float',             label='Z'},                                     -- 10
#    {ctype='float',             label='Y'},                                     -- 14
#    {ctype='bit[13]',           label='Run Count'},                             -- 18:0 Analogue to Run Count from outgoing 0x015
#    {ctype='bit[3]',            label='_unknown3'},                             -- 19:5 Analogue to Run Count from outgoing 0x015
#    {ctype='boolbit',           label='_unknown4'},                             -- 1A:0
#    {ctype='bit[15]',           label='Target Index',       fn=index},          -- 1A:1
#    {ctype='unsigned char',     label='Movement Speed'},                        -- 1C   32 represents 100%
#    {ctype='unsigned char',     label='Animation Speed'},                       -- 1D   32 represents 100%
#    {ctype='unsigned char',     label='HP %',               fn=percent},        -- 1E
#    {ctype='unsigned char',     label='Status',             fn=statuses},       -- 1F
#    {ctype='unsigned int',      label='Flags',              fn=bin+{4}},        -- 20
#    {ctype='unsigned char',     label='Linkshell Red'},                         -- 24
#    {ctype='unsigned char',     label='Linkshell Green'},                       -- 25
#    {ctype='unsigned char',     label='Linkshell Blue'},                        -- 26
#    {ctype='unsigned char',     label='_unknown5'},                             -- 27   Probably junk from the LS color dword
#    {ctype='data[0x1B]',        label='_unknown6'},                             -- 28   DSP notes that the 6th bit of byte 54 is the Ballista flag
#    {ctype='unsigned char',     label='Face Flags'},                            -- 43   0, 3, 4, or 8
#    {ctype='data[4]',           label='_unknown7'},                             -- 44
#    {ctype='unsigned char',     label='Face'},                                  -- 48
#    {ctype='unsigned char',     label='Race'},                                  -- 49
#    {ctype='unsigned short',    label='Head'},                                  -- 4A
#    {ctype='unsigned short',    label='Body'},                                  -- 4C
#    {ctype='unsigned short',    label='Hands'},                                 -- 4E
#    {ctype='unsigned short',    label='Legs'},                                  -- 50
#    {ctype='unsigned short',    label='Feet'},                                  -- 52
#    {ctype='unsigned short',    label='Main'},                                  -- 54
#    {ctype='unsigned short',    label='Sub'},                                   -- 56
#    {ctype='unsigned short',    label='Ranged'},                                -- 58
#    {ctype='char*',             label='Character Name'},                        -- 5A -   *
#}

class iNPCUpdate(template):
    def __init__(self):
        super().__init__(0,0x0e, direction=0, notes='Packet contains data about nearby targets (i.e. target\'s position, name).')

class iIncomingChat(template):
    def __init__(self):
        super().__init__(0,0x17, direction=0, notes='Packet contains data about incoming chat messages.')
        self.fields['mode'] = uint8(0x04, lambda val: ffxi_supportClasses.chatMode[val])
        self.fields['GM'] = uint8(0x05)
        self.fields['zone'] = ushort(0x06)
        self.fields['senderName'] = field(0x08, 16, nullTerminatedString)
        self.fields['Message'] = varString(0x18)
   

class iJobInfo(template):
    def __init__(self):
        super().__init__(0,0x1b, direction=0, notes='Job Levels and levels unlocked.')
        self.fields['_unknown1'] = ulong(0x04)
        self.fields['MainJob'] = uint8(0x08)
        self.fields['FlagOrMainJobLevel?'] = uint8(0x09, binField)
        self.fields['FlagOrSubJobLevel?'] = uint8(0x0a, binField)
        self.fields['SubJob'] = uint8(0x0b)
        self.fields['_JobUnlockFlags'] = ulong(0x0c, binField) #parse out bit field ? 
        self.fields['_unkonwn3' ] = uint8(0x10)
        self.fields['JobLevels'] = jobGroup(0x11, count=0x0f)
        self.fields['baseStats'] = statGroup(0x20)
        self.fields['_unknown4'] = field(0x2e, 14)
        self.fields['MaxHP'] = ulong(0x3c)
        self.fields['MaxMP'] = ulong(0x40)
        self.fields['Flags'] = ulong(0x44, postFilter=binField)
        self.fields['_Unknown5'] = uint8(0x48)
        self.fields['jobLevels2'] = jobGroup(0x49)
        self.fields['CurrentMonsterLevel'] = uint8(0x5f)
        self.fields['EncumbranceFlags'] = ulong(0x60, binField)  #[legs, hands, body, head, ammo, range, sub, main,] [back, right_ring, left_ring, right_ear, left_ear, waist, neck, feet] [HP, CHR, MND, INT, AGI, VIT, DEX, STR,] [X X X X X X X MP]


class iInventoryCount(template):
    def __init__(self):
        super().__init__(0,0x1c, direction=0, notes='Describes number of slots in inventory.')
        self.fields['InventorySize'] = uint8(0x04)
        self.fields['SafeSize'] = uint8(0x05)
        self.fields['StorageSize'] = uint8(0x06)
        self.fields['TemporarySize'] = uint8(0x07)
        self.fields['LockerSize'] = uint8(0x08)
        self.fields['SatchelSize'] = uint8(0x09)
        self.fields['SackSize'] = uint8(0x0a)
        self.fields['CaseSize'] = uint8(0x0b)
        self.fields['WardrobeSize'] = uint8(0x0c)
        self.fields['Safe2Size'] = uint8(0x0d)
        self.fields['Wardrobe2Size'] = uint8(0x0e)
        self.fields['Wardrobe3Size'] = uint8(0x0f)
        self.fields['Wardrobe4Size'] = uint8(0x10)
        self.fields['_padding1'] = field(0x11, 3)
        self.fields['dupInventorySize']  = ushort(0x14)
        self.fields['dupSafeSize']  = ushort(0x16)
        self.fields['dupStorageSize']  = ushort(0x18)
        self.fields['dupTemporarySize']  = ushort(0x1a)
        self.fields['dupLockerSize']  = ushort(0x1c)
        self.fields['dupSatchelSize']  = ushort(0x1e)
        self.fields['dupSackSize']  = ushort(0x20)
        self.fields['dupCaseSize']  = ushort(0x22)
        self.fields['dupWardrobeSize']  = ushort(0x24)
        self.fields['dupSafe2Size']  = ushort(0x26)
        self.fields['dupWardrobe2Size']  = ushort(0x28)
        self.fields['dupWardrobe3Size']  = ushort(0x2a)
        self.fields['dupWardrobe4Size']  = ushort(0x2c)
        self.fields['_padding2'] = field(0x2e,6)

        
        
class iFinishInventory(template):
    def __init__(self):
        super().__init__(0,0x1d, direction=0, notes='Finish listing the items in inventory.')
        self.fields['Flag'] = uint8(0x04)
        self.fields['_junk1'] = field(0x05,3)

class iModifyInventory(template):
    def __init__(self):
        super().__init__(0,0x1e, direction=0, notes='Modifies items in your inventory.')
        self.fields['Count'] = ulong(0x04)
        self.fields['Bag'] = uint8(0x08)
        self.fields['Index'] = uint8(0x09)
        self.fields['Status'] = uint8(0x0a, lambda val:ffxi_supportClasses.itemstat[val])
        self.fields['_junk1'] = uint8(0x0b)

class iItemAssign(template):
    def __init__(self):
        super().__init__(0,0x1f, direction=0, notes='Assigns an ID to equipped items in your inventory.')
        self.fields['Count'] = ulong(0x04)
        self.fields['Item'] = ushort(0x08, lambda val: ffxi_supportClasses.items[val])
        self.fields['Bag'] = uint8(0x0a)
        self.fields['Index'] = uint8(0x0b)
        self.fields['Status'] = uint8(0x0c, lambda val:ffxi_supportClasses.itemstat[val])

class iItemUpdate(template):
    def __init__(self):
        super().__init__(0,0x20, direction=0, notes='Info about item in your inventory.')
        self.fields['Count'] = ulong(0x04)
        self.fields['Bazaar'] = ulong(0x08)
        self.fields['Item'] = ushort(0x0c, lambda val: ffxi_supportClasses.items[val])
        self.fields['Bag'] = uint8(0x0e)
        self.fields['Index'] = uint8(0x0f)
        self.fields['Status'] = uint8(0x10, lambda val: ffxi_supportClasses.itemstat[val])
        self.fields['ExtData'] = field(0x11,24)
        self.fields['_junk1'] = field(0x29, 3)

class iTradeRequested(template):
    def __init__(self):
        super().__init__(0,0x21, direction=0, notes='Sent when somebody offers to trade with you.')
        self.fields['PlayerId'] = ulong(0x04)
        self.fields['Index'] = ushort(0x08)
        self.fields['_junk1'] = ushort(0x0a)

class iTradeAction(template):
    TradeType = { 0:'Trade started', 1:'Trade cancelled', 2:'Trade Accepted By Other Party',9:'Trade Successful' }

    def __init__(self):
        super().__init__(0,0x22, direction=0, notes='Sent whenever something happens with the trade window.')
        self.fields['PlayerId'] = ulong(0x04)
        self.fields['Type'] = ulong(0x08)
        self.fields['Index'] = ushort(0x0c)
        self.fields['_junk1'] = ushort(0x0e)
        #self.fields['TypeParsed'] = iTradeAction.TradeType[self.fields['Type']]

class iTradeItem(template):
    def __init__(self):
        super().__init__(0,0x23, direction=0, notes='Sent when an item appears in the trade window.')
        self.fields['Count'] = ulong(0x04)
        self.fields['TradeCount'] = ushort(0x08)
        self.fields['Item'] = ushort(0x0a)
        self.fields['_unknown1'] = uint8(0x0c)
        self.fields['Slot'] = uint8(0x0d)
        self.fields['ExtData'] = field(0x0e, 24)
        self.fields['_junk1'] = field(0x26, 2)

class iItemAccepted(template):
    def __init__(self):
        super().__init__(0,0x25, direction=0, notes='Sent when the server will allow you to trade an item.')
        self.fields['Count'] = ulong(0x04)
        self.fields['Item'] = ushort(0x08)
        self.fields['Slot'] = uint8(0x0a)
        self.fields['InventoryIndex'] = uint8(0x0b)


class iCountTo80(template):
    def __init__(self):
        super().__init__(0,0x26, direction=0, notes='It counts to 80 and does not have any obvious function. May have something to do with populating inventory.')
        self.fields['_unknown1'] = field(0x04,1)
        self.fields['Slot'] = uint8(0x05)
        self.fields['_unknown2'] = field(0x06,22)

class iStringMessage(template):
    def __init__(self):
        super().__init__(0,0x27, direction=0, notes='Message that includes a string as a parameter.')
        self.fields['PlayerId'] = ulong(0x04)  #0x0112413A in Omen, 0x010B7083 in Legion, Layer Reserve ID for Ambuscade queue, 0x01046062 for Chocobo circuit
        self.fields['PlayerIndex'] = ushort(0x08) #0x013A in Omen, 0x0083 in Legion , Layer Reserve Index for Ambuscade queue, 0x0062 for Chocobo circuit
        self.fields['MessageId'] = ushort(0x0a) #fn=sub+{0x8000}},            -- 0A   -0x8000 --silver: I dont know what this is
        self.fields['Type'] = ulong(0x0c)
        self.fields['Param1'] = ulong(0x10)
        self.fields['Param2'] = ulong(0x14)
        self.fields['Param3'] = ulong(0x18)
        self.fields['Param4'] = ulong(0x1c)
        self.fields['PlayerName'] = field(0x20,16)
        self.fields['_unknown6'] = field(0x30,16)
        self.fields['_dupePlayerName'] = field(0x40,16)
        self.fields['_unknown7'] = field(0x50,32)

class iAction(template):
    def __init__(self):
        super().__init__(0,0x28, direction=0, notes='Packet sent when an NPC is attacking.')

class iActionMessage(template):
    def __init__(self):
        super().__init__(0,0x29, direction=0, notes='Packet sent for simple battle-related messages.')
        self.fields['Actor'] = ulong(0x04)
        self.fields['Target'] = ulong(0x08)
        self.fields['Param1'] = ulong(0x0c)
        self.fields['Param2'] = ulong(0x10)
        self.fields['ActorIdx'] = ushort(0x14)
        self.fields['TargetIdx'] = ushort(0x16)
        self.fields['Message'] = ushort(0x18, lambda val: ffxi_supportClasses.messages[val])
        self.fields['_unknown1'] = ushort(0x1a)


class iResettingMessage(template):
    def __init__(self):
        super().__init__(0,0x2a, direction=0, notes='Packet sent when you rest in Abyssea.')
        self.fields['PlayerId'] = ulong(0x04)
        self.fields['Param1'] = ulong(0x08)
        self.fields['Param2' ] = ulong(0x0c)
        self.fields['Param3'] = ulong(0x10)
        self.fields['Param4'] = ulong(0x14)
        self.fields['PlayerIdx'] = ushort(0x18)
        self.fields['MessageId'] = ushort(0x1a)
        self.fields['_unknown1'] = ulong(0x1c)

class iKillMessage(template):
    def __init__(self):
        super().__init__(0,0x2d, direction=0, notes='Packet sent when you gain XP/LP/CP/JP/MP, advance RoE objectives, etc. by defeating a mob.')
        self.fields['PlayerId'] = ulong(0x04)
        self.fields['target'] = ulong(0x08)  #player if RoE
        self.fields['PlayerIdx'] = ushort(0x0c)
        self.fields['TargIdx'] = ushort(0x0e)
        self.fields['Param1'] = ulong(0x10)
        self.fields['Param2'] = ulong(0x14)
        self.fields['Message'] = ushort(0x18, lambda val: ffxi_supportClasses.messages[val])
        self.fields['_flag1'] = ushort(0x1a)
        
class iMogHouseMenu(template):
    def __init__(self):
        super().__init__(0,0x2e, direction=0, notes='Sent when talking to moogle inside mog house.')

class iDiggingAnimation(template):
    def __init__(self):
        super().__init__(0,0x2f, direction=0, notes='Generates the chocobo digging animation')
        self.fields['PlayerId'] = ulong(0x04)
        self.fields['PlayerIdx'] = ushort(0x08)
        self.fields['Animation'] = uint8(0x0a)
        self.fields['_junk1'] = uint8(0x0b)        

class iSynthAnimation(template):
    def __init__(self):
        super().__init__(0,0x30, direction=0, notes='Generates the synthesis animation')
        self.fields['PlayerId'] = ulong(0x04)
        self.fields['PlayerIdx'] = ushort(0x08)
        self.fields['Effects'] = ushort(0x0a)
        self.fields['Param'] = uint8(0x0c)
        self.fields['Animation'] = uint8(0x0d)
        self.fields['_unknown1'] = uint8(0x0e)

class iSynthList(template):
    def __init__(self):
        super().__init__(0,0x31, direction=0, notes='List of recipes or materials needed for a recipe')
        self.fields['fieldArray'] = field(0x04,48)
        self.notes = self.notes + '\n' + '''
-- Synth List / Synth Recipe
--[[ This packet is used for list of recipes, but also for details of a specific recipe.

   If you ask the guild NPC that provides regular Image Suppor for recipes, 
   s/he will give you a list of recipes, fields are as follows:
   Field1-2: NPC ID
   Field3: NPC Index
   Field4-6: Unknown
   Field7-22: Item ID of recipe
   Field23: Unknown
   Field24: Usually Item ID of the recipe on next page


   If you ask a guild NPC for a specific recipe, fields are as follows:   
   field1: item to make (item id)
   field2,3,4: sub-crafts needed. Note that main craft will not be listed.
      1 = woodworking
      2 = smithing
      3 = goldsmithing
      4 = clothcraft    
      5 = leatherworking
      6 = bonecraft
      7 = Alchemy
      8 = Cooking
   field5: crystal (item id)
   field6: KeyItem needed, if any (in Big Endian)
   field7-14: material required (item id)
   field15-22: qty for each material above.
   field23-24: Unknown   
 ]]'''


class iNPCInteraction1(template):
    def __init__(self):
        super().__init__(0,0x32, direction=0, notes='Occurs before menus and some cutscenes')
        self.fields['NPC'] = ulong(0x04)
        self.fields['NPCIdx'] = ushort(0x08)
        self.fields['Zone'] = ushort(0x0a)
        self.fields['MenuId'] = ushort(0x0c)
        self.fields['_unkonwn1'] = ushort(0x0e)
        self.fields['_dupZone'] = uint8(0x10)
        self.fields['_junk1'] = field(0x11, 3)

class iStringNPCInteraction(template):
    def __init__(self):
        super().__init__(0,0x33, direction=0, notes='Triggers a menu or cutscene to appear. Contains 4 strings.')
        self.fields['NPC'] = ulong(0x04)
        self.fields['NPCIdx'] = ushort(0x08)
        self.fields['Zone'] = ushort(0x0a)
        self.fields['MenuId'] = ushort(0x0c)
        self.fields['_unknown1'] = ushort(0x0e)
        self.fields['NPCName'] = field(0x10,16)
        self.fields['_dupNPCName1'] = field(0x20,16)
        self.fields['_dupNPCName2'] = field(0x30,16)
        self.fields['_dupNPCName3'] = field(0x40,16)
        self.fields['MenuParams'] = field(0x50,32)


class iNPCInteraction2(template):
    def __init__(self):
        super().__init__(0,0x34, direction=0, notes='Occurs before menus and some cutscenes')
        self.fields['NPC'] = ulong(0x04)
        self.fields['MenuParms'] = field(0x08, 32)
        self.fields['NPCIdx'] = ushort(0x28)
        self.fields['Zone'] = ushort(0x2a)
        self.fields['MenuId'] = ushort(0x2c)
        self.fields['_unknown1'] = ushort(0x2e)
        self.fields['_dupZone'] = ushort(0x30)
        self.fields['_junk1'] = field(0x31, 2)

class iNPCChat(template):
    def __init__(self):
        super().__init__(0,0x36, direction=0, notes='Dialog from NPC\'s.')
        self.fields['ActorId'] = ulong(0x04)
        self.fields['ActorIdx'] = ushort(0x08)
        self.fields['MessageId'] = ushort(0x0a)
        self.fields['_Unknown2'] = ulong(0x0c)
        self.notes = self.notes + '\n' + '''#--- When messages are fishing related, the player is the Actor.
#--- For some areas, the most significant bit of the message ID is set sometimes.
#-- NPC Chat'''

class iUpdateChar(template):
    def __init__(self):
        super().__init__(0,0x37, direction=0, notes='Updates a characters stats and animation.')
        pass # this packet is stupid, too many bit fields.. work out bit field & derived packet types first


class iEntityAnimation(template):
    def __init__(self):
        super().__init__(0,0x38, direction=0, notes='Sent when a model should play a specific animation.')
        self.fields['Mob'] = ulong(0x04)
        self.fields['_dupMob'] = ulong(0x08)
        self.fields['Type'] = field(0x0c, 4)
        self.fields['MobIdx'] = ushort(0x10)
        self.fields['_dupMobIdx'] = ushort(0x12)

class iEnvAnimation(template):
    def __init__(self):
        super().__init__(0,0x39, direction=0, notes='Sent to force animations to specific objects.')
        self.fields['ID'] = ulong(0x04)
        self.fields['dupID'] = ulong(0x08)
        self.fields['Type'] = field(0x0c, 4)
        self.fields['Index'] = ushort(0x10)
        self.fields['dupIdx'] = ushort(0x12)


class iIndependAnimation(template):
    def __init__(self):
        super().__init__(0,0x3a, direction=0, notes='Used for arbitrary battle animations that are unaccompanied by an action packet.')
        self.fields['ActorId'] = ulong(0x04)
        self.fields['TargetId'] = ulong(0x08)
        self.fields['ActorIdx'] = ushort(0x0c)
        self.fields['TargetIdx'] = ushort(0x0e)
        self.fields['AnimationId'] = ushort(0x10)
        self.fields['AnimationType'] = uint8(0x12)
        self.fields['_junk1'] = uint8(0x13)

class iShop(template):
    def __init__(self):
        super().__init__(0,0x3c, direction=0, notes='Displays items in a vendors shop.')
        self.fields['_zero1'] = ushort(0x04)
        self.fields['_padding1'] = ushort(0x06)
        self.fields['Item'] = shopItem(0x08)

class iValue(template):
    def __init__(self):
        super().__init__(0,0x3d, direction=0, notes='Returns the value of an item.')
        self.fields['Price'] = ulong(0x04)
        self.fields['InventoryIdx'] = uint8(0x08)
        self.fields['Bag'] = uint8(0x09)
        self.fields['_junk1'] = ushort(0x0a)
        self.fields['_unknown1'] = ulong(0x0c)

class iOpenBuySell(template):
    def __init__(self):
        super().__init__(0,0x3e, direction=0, notes='Opens the buy/sell menu for vendors.')
        self.fields['Type'] = uint8(0x04)
        self.fields['_junk1'] = field(0x05, 3)

class iShopBuyResponse(template):
    def __init__(self):
        super().__init__(0,0x3f, direction=0, notes='Sent when you buy something from normal vendors.')
        self.fields['ShopSlot'] = ushort(0x04)
        self.fields['_unkonwn1'] = ushort(0x06)
        self.fields['Count'] = ulong(0x08)

class iBlacklist(template):
    def __init__(self):
        super().__init__(0,0x41, direction=0, notes='Contains player ID and name for blacklist.')
        self.fields['BlackListEntries'] = blacklistEntry(0x08, count=12)
        self.fields['_unkonwn3'] = uint8(0xf4)
        self.fields['Size'] = uint8(0xf5)

class iBlacklistCommand(template):
    def __init__(self):
        super().__init__(0,0x42, direction=0, notes='Sent in response to /blacklist add or /blacklist delete.')
        self.fields['_unkonwn1'] = ulong(0x04)
        self.fields['Name'] = field(0x08, 16)
        self.fields['AddRemove'] = uint8(0x18)
        self.fields['_unknown2'] = field(0x19, 3)

class iJobInfoExtra(template):
    def __init__(self):
        super().__init__(0,0x44, direction=0, notes='Contains information about Automaton stats and set Blue Magic spells.')
        pass #more work to do


class iTranslateResponse(template):
    def __init__(self):
        super().__init__(0,0x47, direction=0, notes='Response to a translate request.')
        self.fields['AutotranslateCode'] = ushort(0x04)
        self.fields['StartingLanguage'] = uint8(0x06)
        self.fields['EndingLanguage'] = uint8(0x07)
        self.fields['InitialPhrase'] = field(0x08, 64)
        self.fields['TranslatedPhrase'] = field(0x48, 64)

#class iLogoutAck(template):
#    def __init__(self):
#        super().__init__(0,0x48, direction=0, notes='Acknowledges a logout attempt.')

class iDeliveryItem(template):
    def __init__(self):
        super().__init__(0,0x4b, direction=0, notes='Item in delivery box.')
        mod = lambda payload: self.fields['Type'].getValue(payload, noFilter) in [1,4,6,8,10]
        self.c = mod
        #base
        self.fields['Type'] = uint8(0x04, postFilter=lambda val:ffxi_supportClasses.DeliveryTypes[val])
        self.fields['_unkonwn1'] = uint8(0x5)
        self.fields['DeliverySlot'] = int8(0x06)
        self.fields['_unknown2'] = long(0x07)
        self.fields['_unkonwn3'] = int8(0x0c)
        self.fields['_unknown4'] = int8(0x0d)
        self.fields['PacketNumber'] = int8(0x0e)
        self.fields['_unknown5'] = short(0x0f)
        self.fields['_unknown6'] = long(0x10)
        self.fields['TargetPlayerName'] = conditional(mod, field(0x14,16, nullTerminatedString))
        self.fields['_unknown8'] = conditional(mod, ulong(0x24))
        self.fields['Timestamp'] = conditional(mod, ulong(0x28))
        self.fields['_Unkonwon9'] = conditional(mod, ulong(0x2c))
        self.fields['Item'] = conditional(mod, ushort(0x30, lambda val:ffxi_supportClasses.items[val]))
        self.fields['_unknown10'] = conditional(mod, ushort(0x32))
        self.fields['Flags'] = conditional(mod, ulong(0x34))
        self.fields['Count'] = conditional(mod, ulong(0x38))
        self.fields['_unknown11'] = conditional(mod, ulong(0x3a))
        self.fields['_unknown12'] = conditional(mod, field(0x3c,28))



class iAuctionHoueMenu(template):
    def __init__(self):
        super().__init__(0,0x4c, direction=0, notes='Sent when visiting auction counter.')
        c1 = lambda payload: self.fields['Type'].getValue(payload, noFilter) == 0x04
        cCommand = lambda payload: self.fields['Type'].getValue(payload, noFilter) in [0x02, 0x03, 0x04,0x05, 0x10]
        type0A = lambda payload: self.fields['Type'].getValue(payload, noFilter) in [0x0a, 0x0b, 0x0d]

        self.fields['Type'] = uint8(0x04, lambda val: ffxi_supportClasses.AhIType[val])  #base
        self.fields['_unknown1'] = uint8(0x05)
        self.fields['Success'] =  conditional(cCommand,uint8(0x06))
        self.fields['_unknown2'] = uint8(0x07)
        self.fields['_junk'] = uint8(0x08)
        self.fields['Fee'] = conditional(c1, ulong(0x08))
        self.fields['InventoryIdx'] = conditional(c1, ushort(0x0c))
        self.fields['Item'] = conditional(c1, ushort(0x0e))
        self.fields['Stack'] = conditional(c1, uint8(0x10))
        self.fields['_junk']=  conditional(c1, field(0x11))

        self.fields['Slot'] =conditional(type0A, uint8(0x05))
        self.fields['_junk1'] = conditional(type0A, field(0x08, 12))
        self.fields['SaleStatus'] = conditional(type0A, uint8(0x14, lambda val: ffxi_supportClasses.AhSaleStat[val]))
        self.fields['_unknown3'] = conditional(type0A, uint8(0x15))
        self.fields['InventoryIdx'] = conditional(type0A, ushort(0x16))
        self.fields['Name']= conditional(type0A, field(0x18,16,nullTerminatedString))
        self.fields['Item'] = conditional(type0A, ushort(0x28, lambda val: ffxi_supportClasses.items[val]))
        self.fields['Count'] = conditional(type0A, uint8(0x2a))
        self.fields['AHCategory'] = conditional(type0A, uint8(0x2b))
        self.fields['Price'] = conditional(type0A, ulong(0x2c))
        self.fields['_unknown6']= conditional(type0A, ulong(0x30))
        self.fields['_unkonwn7'] = conditional(type0A, ulong(0x34))
        self.fields['Timestamp'] = conditional(type0A, ulong(0x38))


        self.notes = self.notes + '\nComplex Type, will need review'

class iServmesResponse(template):
    def __init__(self):
        super().__init__(0,0x4d, direction=0, notes='Server response when someone requests it.')
        self.fields['_unknown1'] = uint8(0x04)
        self.fields['_unknown2'] = uint8(0x05)
        self.fields['_unknown3'] = uint8(0x06)
        self.fields['_unknown4'] = uint8(0x07)
        self.fields['Timestamp'] = ushort(0x08)
        self.fields['MessageLen1'] = ulong(0x0a)
        self.fields['_unknowwn5'] = ulong(0x12)
        self.fields['MessageLen2'] = ulong(0x14)
        self.fields['message'] = varString(0x18)

class iDataDownload2(template):
    def __init__(self):
        super().__init__(0,0x4f, direction=0, notes='The data that is sent to the client when it is "Downloading data...".')
        self.fields['_unknown1'] = long(0x04)

class iEquip(template):
    def __init__(self):
        super().__init__(0,0x50, direction=0, notes='Updates the characters equipment slots.')
        self.fields['InventoryIdx'] = uint8(0x04)
        self.fields['EquipSlot'] = uint8(0x05)
        self.fields['Bag'] = uint8(0x06, lambda val: ffxi_supportClasses.bags[val])
        self.fields['_junk1'] = field(0x07,1)

class iModelChange(template):
    def __init__(self):
        super().__init__(0,0x51, direction=0, notes='Info about equipment and appearance')
        self.fields['Face'] = uint8(0x04)
        self.fields['Race'] = uint8(0x05)
        self.fields['Head'] = ushort(0x06)
        self.fields['Body'] = ushort(0x08)
        self.fields['Hands'] = ushort(0x0a)
        self.fields['Legs'] = ushort(0x0c)
        self.fields['Feet'] = ushort(0x0e)
        self.fields['Main'] = ushort(0x10)
        self.fields['Sub'] = ushort(0x12)
        self.fields['Ranged'] = ushort(0x14)
        self.fields['_unknown1'] = ushort(0x16)
    
class iNPCRelease(template):
    def __init__(self):
        super().__init__(0,0x52, direction=0, notes='Allows your PC to move after interacting with an NPC.')




class iLogoutTime(template):
    def __init__(self):
        super().__init__(0,0x53, direction=0, notes='The annoying message that tells how much time till you logout.')
        self.fields['Param'] = ulong(0x04)
        self.fields['_unknown1'] = ulong(0x08)
        self.fields['MessageId'] = ushort(0x0c)
        self.fields['_unknown2'] = ushort(0x0e)

class iKeyItemLog(template):
    def __init__(self):
        super().__init__(0,0x55, direction=0, notes='Updates your key item log on zone and when appropriate.')
        self.fields['KeyItemsAvailable'] = field(0x04,0x40)
        self.fields['KeyIitemsExamined'] = field(0x44, 0x40)
        self.fields['Type'] = ulong(0x84)       

class iQuestMissionLog(template):
    def __init__(self):
        super().__init__(0,0x56, direction=0, notes='Updates your quest and mission log on zone and when appropriate.')
        self.fields['Type'] = short(0x24)

class iWeatherChange(template):
    def __init__(self):
        super().__init__(0,0x57, direction=0, notes='Updates the weather effect when the weather changes.')
        self.fields['VanaTime'] = ulong(0x04)
        self.fields['Weather'] = uint8(0x08)
        self.fields['_unknown1'] = uint8(0x09)
        self.fields['_unknown2'] = ushort(0x0a)

#class iLockTarget(template):
#    def __init__(self):
#        super().__init__(0,0x58, direction=0, notes='Locks your target.')

class iServerEmote(template):
    def __init__(self):
        super().__init__(0,0x5a, direction=0, notes='This packet is the server\'s response to a client /emote p.')
        self.fields['PlayerId'] = ulong(0x04)
        self.fields['TargetId'] = ulong(0x08)
        self.fields['PlayerIdx'] = ushort(0x0c)
        self.fields['TargetIdx'] = ushort(0x0e)
        self.fields['EmoteId'] = ushort(0x10)
        self.fields['_unknown1'] = ushort(0x12)
        self.fields['_unknown2'] = ushort(0x14)
        self.fields['Type'] = uint8(0x16)
        self.fields['_unknown3'] = uint8(0x17)
        self.fields['_unknown4'] = field(0x18, 32)

class iSpawn(template):
    def __init__(self):
        super().__init__(0,0x5b, direction=0, notes='Server packet sent when a new mob spawns in area.')
        self.fields['X'] = float(0x04)
        self.fields['Y'] = float(0x08)
        self.fields['Z'] = float(0x0c)
        self.fields['Id'] = ulong(0x10)
        self.fields['Index'] = ushort(0x14)
        self.fields['Type'] = uint8(0x16)
        self.fields['_unknown1'] = uint8(0x17)
        self.fields['_unknown2'] = ulong(0x18)

class iDialogueInformation(template):
    def __init__(self):
        super().__init__(0,0x5c, direction=0, notes='Used when all the information required for a menu cannot be fit in an NPC Interaction packet.')
        self.fields['MenuParams'] = field(0x04, 32)
        self.notes = self.notes + '\nComplex field\n' 

class iCampBesiegedMap(template):
    def __init__(self):
        super().__init__(0,0x5e, direction=0, notes='Contains information about Campaign and Besieged status.')
        self.fields['BalanceOfPower'] = uint8(0x04)
        self.fields['AllianceIndicator'] = uint8(0x05)
        self.fields['_unknown1'] = field(0x06, 20)
        self.fields['bpRonfaure'] = ulong(0x1a)
        self.fields['bpZulkheim'] = ulong(0x1e)
        self.fields['bpNorvallen'] = ulong(0x22)
        self.fields['bpGustaberg'] = ulong(0x26)
        self.fields['bpDerfland'] = ulong(0x2a)
        self.fields['bpSarutabaruta'] = ulong(0x2e)
        self.fields['bpKolshushu'] = ulong(0x32)
        self.fields['bpAragoneu'] = ulong(0x36)
        self.fields['bpFauregandi'] = ulong(0x3a)
        self.fields['bpValdeaunia'] = ulong(0x3e)
        self.fields['bpQufim'] = ulong(0x42)
        self.fields['bpLitelor'] = ulong(0x46)
        self.fields['bpKuzotz'] = ulong(0x4a)
        self.fields['bpVollbow'] = ulong(0x4e)
        self.fields['bpElshimoLow'] = ulong(0x52)
        self.fields['bpElshimoHigh'] = ulong(0x56)
        self.fields['bpTulia'] = ulong(0x5a)
        self.fields['bpMovapolos'] = ulong(0x5e)
        self.fields['bpTavnazia'] = ulong(0x62)
        self.fields['_unknown2'] = field(0x66, 32)
        self.fields['SandyRegionBar'] = uint8(0x86)
        self.fields['BastokRegionBar'] = uint8(0x87)
        self.fields['WindurstRegionBar'] = uint8(0x88)
        self.fields['SandyRegionBarWithoutBeastmen'] = uint8(0x89)
        self.fields['BastokRegionBarWithoutBeastmen'] = uint8(0x8a)
        self.fields['WindurstRegionBarWithoutBeastmen'] = uint8(0x8b)
        self.fields['DaysToTally'] = uint8(0x8c)
        self.fields['_unknown4'] = field(0x8d,3)
        self.fields['ConquestPoints'] = long(0x94)
        self.fields['_unknown5'] = field(0x95, 12)
        self.notes = self.notes + '''
#fields.incoming[0x05E] = L{

#-- These bytes are for the overview summary on the map.
#    -- The two least significant bits code for the owner of the Astral Candescence.
#    -- The next two bits indicate the current orders.
#    -- The four most significant bits indicate the MMJ level.
#    {ctype='unsigned char',     label="MMJ Level, Orders, and AC"},             -- A0

#    -- Halvung is the 4 least significant bits.
#    -- Arrapago is the 4 most significant bits.
#    {ctype='unsigned char',     label="Halvung and Arrapago Level"},            -- A1
#    {ctype='unsigned char',     label="Beastman Status (1) "},                  -- A2   The 3 LS bits are the MMJ Orders, next 3 bits are the Halvung Orders, top 2 bits are part of the Arrapago Orders
#    {ctype='unsigned char',     label="Beastman Status (2) "},                  -- A3   The Least Significant bit is the top bit of the Arrapago orders. Rest of the byte doesn't seem to do anything?

#-- These bytes are for the individual stronghold displays. See above!
#    {ctype='unsigned int',      label='Bitpacked MMJ Info'},                    -- A4
#    {ctype='unsigned int',      label='Bitpacked Halvung Info'},                -- A8
#    {ctype='unsigned int',      label='Bitpacked Arrapago Info'},               -- AC

#    {ctype='int',               label='Imperial Standing'},                     -- B0
#}




#-- Campaign/Besieged Map information

#-- Bitpacked Campaign Info:
#-- First Byte: Influence ranking including Beastmen
#-- Second Byte: Influence ranking excluding Beastmen

#-- Third Byte (bitpacked xxww bbss -- First two bits are for beastmen)
#    -- 0 = Minimal
#    -- 1 = Minor
#    -- 2 = Major
#    -- 3 = Dominant

#-- Fourth Byte: Ownership (value)
#    -- 0 = Neutral
#    -- 1 = Sandy
#    -- 2 = Bastok
#    -- 3 = Windurst
#    -- 4 = Beastmen
#    -- 0xFF = Jeuno




#-- Bitpacked Besieged Info:

#-- Candescence Owners:
#    -- 0 = Whitegate
#    -- 1 = MMJ
#    -- 2 = Halvung
#    -- 3 = Arrapago

#-- Orders:
#    -- 0 = Defend Al Zahbi
#    -- 1 = Intercept Enemy
#    -- 2 = Invade Enemy Base
#    -- 3 = Recover the Orb

#-- Beastman Status
#    -- 0 = Training
#    -- 1 = Advancing
#    -- 2 = Attacking
#    -- 3 = Retreating
#    -- 4 = Defending
#    -- 5 = Preparing

#-- Bitpacked region int (for the actual locations on the map, not the overview)
#    -- 3 Least Significant Bits -- Beastman Status for that region
#    -- 8 following bits -- Number of Forces
#    -- 4 following bits -- Level
#    -- 4 following bits -- Number of Archaic Mirrors
#    -- 4 following bits -- Number of Prisoners
#    -- 9 following bits -- No clear purpose
'''


class iMusicChange(template):
    def __init__(self):
        super().__init__(0,0x5f, direction=0, notes='Changes the current music.')
        self.fields['BGMType'] = ushort(0x04)
        self.fields['SOngId'] = ushort(0x06)

class iCharStats(template):
    def __init__(self):
        super().__init__(0,0x61, direction=0, notes='Packet contains a lot of data about your character\'s stats.')
        self.fields['MaxHP'] = ulong(0x04)
        self.fields['MaxMP'] = ulong(0x08)
        self.fields['MainJob'] = uint8(0x0c)
        self.fields['MainJobLevel'] = uint8(0x0d)
        self.fields['SubJob'] = uint8(0x0e)
        self.fields['SubJobLevel'] = uint8(0x1f)
        self.fields['CurrentExp'] = ushort(0x10)
        self.fields['RequiredExp'] = ushort(0x12)
        self.fields['BaseStats'] = statGroup(0x14)
        self.fields['AddedStats'] = statGroup(0x22)
        self.fields['Attack'] = ushort(0x30)
        self.fields['Defense'] = ushort(0x32)
        self.fields['Resistances'] = elementGroup(0x34)
        self.fields['Title'] = ushort(0x44)
        self.fields['NationRank'] = ushort(0x46)
        self.fields['RankPoints'] = ushort(0x48)
        self.fields['HomePoint'] = ushort(0x4a)
        self.fields['_unknown1'] = ushort(0x4c)
        self.fields['_unknown2'] = ushort(0x4e)
        self.fields['Nation'] = uint8(0x50)
        self.fields['_unknown3']= uint8(0x51)
        self.fields['SuLevel'] = uint8(0x52)
        self.fields['_unknown4'] = uint8(0x53)
        self.fields['MaxILvl'] = uint8(0x54)
        self.fields['iLvlOver99'] = uint8(0x55)
        self.fields['MainHandIlvl'] = uint8(0x56)
        self.fields['_unknown5'] = uint8(0x57)
        self.fields['UnityId'] = uint8(0x58) # bit array @ 5
        self.fields['_unknown5'] = uint8(0x58) # bit array, next 5
        self.fields['UnityPoints'] = ushort(0x59)
        self.fields['_unknown6'] = uint8(0x5a)
        self.fields['_junk1'] = uint8(0x5b)
       

class iSkillsUpdate(template):
    def __init__(self):
        super().__init__(0,0x62, direction=0, notes='Packet that shows your weapon and magic skill stats.')
        combatSkillMask = 32767
        combatSkillIsCappedMask = 32768
        craftSkillRankMask = 31
        craftSkillMask = 32736
        craftSkillCapped = 32768
        self.fields['_junk1'] = field(4,124)
        #combat skills  ##review this code!
        self.fields['nullSkill'] = bitField(ushort(0x80),combatSkillMask)
        self.fields['nullSkillIsCapped'] = bitField(ushort(0x80), combatSkillIsCappedMask,15)
        self.fields['H2H'] = bitField(ushort(0x82), combatSkillMask)
        self.fields['H2HIsCapped'] = bitField(ushort(0x82), combatSkillIsCappedMask,15)
        self.fields['Dagger' ] = bitField(ushort(0x84), combatSkillMask)
        self.fields['DaggerIsCapped'] = bitField(ushort(0x84), combatSkillIsCappedMask,15)
        self.fields['Sword'] = bitField(ushort(0x86), combatSkillMask)
        self.fields['SwordIsCapped'] = bitField(ushort(0x86), combatSkillIsCappedMask,15)
        self.fields['GreatSword'] = bitField(ushort(0x88), combatSkillMask)
        self.fields['GreatSwordISCapped'] = bitField(ushort(0x88), combatSkillIsCappedMask,15)
        self.fields['Axe'] = bitField(ushort(0x8a), combatSkillMask)
        self.fields['AxeIsCapped'] = bitField(ushort(0x8a), combatSkillIsCappedMask,15)
        self.fields['GreatAxe'] = bitField(ushort(0x8c), combatSkillMask)
        self.fields['GreatAxeIsCapped'] = bitField(ushort(0x8c), combatSkillIsCappedMask,15)  
        self.fields['Scythe'] = bitField(ushort(0x8e), combatSkillMask)
        self.fields['ScytheIsCapped'] = bitField(ushort(0x8e), combatSkillIsCappedMask,15)
        self.fields['Polearm'] = bitField(ushort(0x90), combatSkillMask)
        self.fields['PolearmISCapped'] = bitField(ushort(0x90), combatSkillIsCappedMask,15)
        self.fields['Katana'] = bitField(ushort(0x92), combatSkillMask)
        self.fields['KatanaIsCapped'] = bitField(ushort(0x92), combatSkillIsCappedMask,15)
        self.fields['GreatKatana'] = bitField(ushort(0x94), combatSkillMask)
        self.fields['GreatKatanaIsCapped'] = bitField(ushort(0x94), combatSkillIsCappedMask,15)
        self.fields['Club'] = bitField(ushort(0x96), combatSkillMask)
        self.fields['ClubIsCapped'] = bitField(ushort(0x96), combatSkillIsCappedMask,15)
        self.fields['Staff'] = bitField(ushort(0x98), combatSkillMask)
        self.fields['StaffIsCapped'] = bitField(ushort(0x98), combatSkillIsCappedMask,15)
        #automata skills
        self.fields['aMelee'] = bitField(ushort(0x9a), combatSkillMask)
        self.fields['aMeleeIsCapped'] = bitField(ushort(0x9a), combatSkillIsCappedMask,15)
        self.fields['aArchery'] = bitField(ushort(0x9c), combatSkillMask)
        self.fields['aArcheryIsCapped'] = bitField(ushort(0x9c), combatSkillIsCappedMask,15)
        self.fields['aMagic'] = bitField(ushort(0x9e), combatSkillMask)
        self.fields['aMagicIsCapped'] = bitField(ushort(0x9e), combatSkillIsCappedMask,15)
        
        #combatSkills2
        self.fields['Archery'] = bitField(ushort(0xa0), combatSkillMask)
        self.fields['ArcheryIsCapped'] = bitField(ushort(0xa0), combatSkillIsCappedMask,15)
        self.fields['Marksmanship' ]= bitField(ushort(0xa2), combatSkillMask)
        self.fields['MarksmanshipIsCapped'] = bitField(ushort(0xa2), combatSkillIsCappedMask,15)
        self.fields['Throwing'] = bitField(ushort(0xa4), combatSkillMask)
        self.fields['ThrowingIsCapped'] = bitField(ushort(0xa4), combatSkillIsCappedMask,15)
        self.fields['Guard'] = bitField(ushort(0xa6), combatSkillMask)
        self.fields['GuardIsCapped' ] = bitField(ushort(0xa6), combatSkillIsCappedMask,15)
        self.fields['Evasion'] = bitField(ushort(0xa8), combatSkillMask)
        self.fields['EvasionIsCapped' ] = bitField(ushort(0xa8), combatSkillIsCappedMask,15)
        self.fields['Shield'] = bitField(ushort(0xaa), combatSkillMask)
        self.fields['ShieldIsCapped'] = bitField(ushort(0xaa), combatSkillIsCappedMask,15)
        self.fields['Parrying'] = bitField(ushort(0xac), combatSkillMask)
        self.fields['ParryingIsCapped'] = bitField(ushort(0xac), combatSkillIsCappedMask,15)

        #magic skills
        self.fields['mDivine'] = bitField(ushort(0xae), combatSkillMask)
        self.fields['mDivineIsCapped' ] = bitField(ushort(0xae), combatSkillIsCappedMask,15)
        self.fields['mHealing'] = bitField(ushort(0xb0), combatSkillMask)
        self.fields['mHealingIsCapped' ] = bitField(ushort(0xb0), combatSkillIsCappedMask,15)
        self.fields['mEnhancing' ] = bitField(ushort(0xb2), combatSkillMask)
        self.fields['mEnhancingISCapped' ] = bitField(ushort(0xb2), combatSkillIsCappedMask,15)
        self.fields['mEnfeebling' ] = bitField(ushort(0xb4), combatSkillMask)
        self.fields['mEnfeeblingIsCapped'] = bitField(ushort(0xb4), combatSkillIsCappedMask,15)
        self.fields['mElemenetal'] = bitField(ushort(0xb6), combatSkillMask)
        self.fields['mElementalIsCapped' ] = bitField(ushort(0xb6), combatSkillIsCappedMask,15)
        self.fields['mDark'] = bitField(ushort(0xb8), combatSkillMask)
        self.fields['mDarkIsCapped' ] = bitField(ushort(0xb8), combatSkillIsCappedMask,15)
        self.fields['mSummoning'] = bitField(ushort(0xba), combatSkillMask)
        self.fields['mSummoningIsCapped' ] = bitField(ushort(0xba), combatSkillIsCappedMask,15)
        self.fields['mNinjutsu'] = bitField(ushort(0xbc), combatSkillMask)
        self.fields['mNinjutsuIsCapped'] = bitField(ushort(0xbc), combatSkillIsCappedMask,15)
        self.fields['mString'] = bitField(ushort(0xbe), combatSkillMask)
        self.fields['mStringIsCapped' ] = bitField(ushort(0xbe), combatSkillIsCappedMask,15)
        self.fields['mSinging' ] = bitField(ushort(0xc0), combatSkillMask)
        self.fields['mSingingIsCapped'] = bitField(ushort(0xc0), combatSkillIsCappedMask,15)
        self.fields['mString'] = bitField(ushort(0xc2), combatSkillMask)
        self.fields['mStringIsCapped'] = bitField(ushort(0xc2), combatSkillIsCappedMask,15)
        self.fields['mWind'] = bitField(ushort(0xc4), combatSkillMask)
        self.fields['mWindIsCapped'] = bitField(ushort(0xc4), combatSkillIsCappedMask,15)
        self.fields['mBlue'] = bitField(ushort(0xc6), combatSkillMask)
        self.fields['mBlueIsCapped' ] = bitField(ushort(0xc6), combatSkillIsCappedMask,15)    
        self.fields['mGeo'] = bitField(ushort(0xc8), combatSkillMask)
        self.fields['mGeoIsCapped' ] = bitField(ushort(0xc8), combatSkillIsCappedMask,15)
        self.fields['mHandbell'] = bitField(ushort(0xca), combatSkillMask)
        self.fields['mHandbellIsCapped' ] = bitField(ushort(0xca), combatSkillIsCappedMask,15)
        #no idea what this is
        #self.fields['_unknown_silver1'] = field(0xcc,0x60)
        
        #craftskills
        self.fields['cFishing' ] = bitField(ushort(0xe0), craftSkillMask,5)
        self.fields['cFishingRank' ] = bitField(ushort(0xe0), craftSkillRankMask)
        self.fields['cFishingIsCapped'] = bitField(ushort(0xe0), craftSkillCapped,15)

        self.fields['cWoodworking'] = bitField(ushort(0xe2), craftSkillMask,5)
        self.fields['cWoodworkingRank' ] = bitField(ushort(0xe2), craftSkillRankMask)
        self.fields['cWoodworkingIsCapped' ] = bitField(ushort(0xe2), craftSkillCapped,15)
        
        self.fields['cSmithing' ] = bitField(ushort(0xe4), craftSkillMask,5)
        self.fields['cSmithingRank' ] = bitField(ushort(0xe4), craftSkillRankMask)
        self.fields['cSmithingIsCapped' ] = bitField(ushort(0xe4), craftSkillCapped,15)
        
        self.fields['cGoldsmithing' ] = bitField(ushort(0xe6), craftSkillMask,5)
        self.fields['cGoldsmithingRank' ] = bitField(ushort(0xe6), craftSkillRankMask)
        self.fields['cGoldsmithingIsCapped' ] = bitField(ushort(0xe6), craftSkillCapped,15)

        self.fields['cClothcraft' ] = bitField(ushort(0xe8), craftSkillMask,5)
        self.fields['cClothcraftRank'] = bitField(ushort(0xe8), craftSkillRankMask)
        self.fields['cClothcraftIsCapped' ] = bitField(ushort(0xe8), craftSkillCapped,15)
        
        self.fields['cLeathercraft'] = bitField(ushort(0xea), craftSkillMask,5)
        self.fields['cLeathercraftRank'] = bitField(ushort(0xea), craftSkillRankMask)
        self.fields['cLeathercraftIsCapped' ] = bitField(ushort(0xea), craftSkillCapped,15)
        
        self.fields['cBonecraft'] = bitField(ushort(0xec), craftSkillMask,5)
        self.fields['cBonecraftRank'] = bitField(ushort(0xec), craftSkillRankMask)
        self.fields['cBonecraftIsCapped'] = bitField(ushort(0xec), craftSkillCapped,15)

        self.fields['cAlchemy'] = bitField(ushort(0xee), craftSkillMask,5)
        self.fields['cAlchemyRank'] = bitField(ushort(0xee), craftSkillRankMask)
        self.fields['cAlchemyIsCapped'] = bitField(ushort(0xee), craftSkillCapped,15)

        self.fields['cCooking'] = bitField(ushort(0xf0), craftSkillMask,5)
        self.fields['cCookingRank'] = bitField(ushort(0xf0), craftSkillRankMask)
        self.fields['cCookingIsCapped'] = bitField(ushort(0xf0), craftSkillCapped,15)
    
        self.fields['cSynergy' ] = bitField(ushort(0xf2), craftSkillMask,5)
        self.fields['cSynergyRank'] = bitField(ushort(0xf2), craftSkillRankMask)
        self.fields['cSynergyIsCapped'] = bitField(ushort(0xf2), craftSkillCapped,15)

        self.fields['_junk2'] = field(0xf4,12)

class iSetUpdate(template):
    def __init__(self):
        super().__init__(0,0x63, direction=0, notes='Frequently sent packet during battle that updates specific types of job information, like currently available/set automaton equipment and currently set BLU spells.')

class iRepositioning(template):
    def __init__(self):
        super().__init__(0,0x65, direction=0, notes='Moves your character. Seems to be functionally idential to the Spawn packet')
        self.fields['X'] = float(0x04)
        self.fields['Z'] = float(0x08)
        self.fields['Y'] = float(0x0c)
        self.fields['Id'] = ulong(0x10)
        self.fields['Idx'] = ushort(0x14)
        self.fields['_unknown1'] = uint8(0x16)
        self.fields['_unknown2'] = uint8(0x17)
        self.fields['_unknown3'] = field(0x18, 6)

class iPetInfo(template):
    def __init__(self):
        super().__init__(0,0x67, direction=0, notes='Updates information about whether or not you have a pet and the TP, HP, etc. of the pet if appropriate.')

class iPetStatus(template):
    def __init__(self):
        super().__init__(0,0x68, direction=0, notes='Updates information about whether or not you have a pet and the TP, HP, etc. of the pet if appropriate.')

class iSelfSynthResults(template):
    def __init__(self):
        super().__init__(0,0x6f, direction=0, notes='Results of an attempted synthesis process by yourself.')
        self.fields['Result'] = uint8(0x04)
        self.fields['Quality'] = uint8(0x05)
        self.fields['Count'] = uint8(0x06)
        self.fields['_junk1'] = uint8(0x07)
        self.fields['Item'] = ushort(0x08, lambda x: ffxi_supportClasses.items[x])
        self.fields['LostItem1'] = ushort(0x0a)
        self.fields['LostItem2'] = ushort(0x0c)
        self.fields['LostItem3'] = ushort(0x0e)
        self.fields['LostItem4'] = ushort(0x10)
        self.fields['LostItem5'] = ushort(0x12)
        self.fields['LostItem6'] = ushort(0x14)
        self.fields['LostItem7'] = ushort(0x16)
        self.fields['LostItem8'] = ushort(0x18)
        self.fields['Skill'] = field(0x1a,4)  #skill type identifier, 0x33 appears to be goldsmithing, 0x31 woodworking
        self.fields['SkillUp'] = field(0x1e, 4)  #skill up value
        self.fields['Crystal'] = ushort(0x22, lambda x: ffxi_supportClasses.items[x])


class iOtherSynthResults(template):
    def __init__(self):
        super().__init__(0,0x70, direction=0, notes='Results of an attempted synthesis process by others.')
        self.fields['Result'] = uint8(0x04)
        self.fields['Quality'] = uint8(0x05)
        self.fields['Count'] = uint8(0x06)
        self.fields['_junk1'] = uint8(0x07)
        self.fields['Item'] = ushort(0x08)
        self.fields['LostItem1'] = ushort(0x0a)
        self.fields['LostItem2'] = ushort(0x0c)
        self.fields['LostItem3'] = ushort(0x0e)
        self.fields['LostItem4'] = ushort(0x10)
        self.fields['LostItem5'] = ushort(0x12)
        self.fields['LostItem6'] = ushort(0x14)
        self.fields['LostItem7'] = ushort(0x16)
        self.fields['LostItem8'] = ushort(0x18)
        self.fields['Skill'] = field(0x1a, 4)
        self.fields['PlayerName'] = field(0x1e, 16)


class iCampaignMapInfo(template):
    def __init__(self):
        super().__init__(0,0x71, direction=0, notes='Populates the Campaign map.')

class iUnityStart(template):
    def __init__(self):
        super().__init__(0,0x75, direction=0, notes='Creates the timer and glowing fence that accompanies Unity fights.')

class iPartyBuffs(template):
    def __init__(self):
        super().__init__(0,0x76, direction=0, notes='Packet updated every time a party member\'s buffs change.')

class iProposal(template):
    def __init__(self):
        super().__init__(0,0x78, direction=0, notes='Carries proposal information from a /propose or /nominate command.')

class iProposalUpdate(template):
    def __init__(self):
        super().__init__(0,0x79, direction=0, notes='Proposal update following a /vote command.')

class iGuildBuyMessage(template):
    def __init__(self):
        super().__init__(0,0x82, direction=0, notes='Buy an item from a guild.')

class iGuildInvList(template):
    def __init__(self):
        super().__init__(0,0x83, direction=0, notes='Provides the items, prices, and counts for guild inventories.')

class iGuildSellResponse(template):
    def __init__(self):
        super().__init__(0,0x84, direction=0, notes='Sell an item to a guild.')

class iGuildSaleList(template):
    def __init__(self):
        super().__init__(0,0x85, direction=0, notes='Provides the items, prices, and counts for guild inventories.')

class iGuildOpen(template):
    def __init__(self):
        super().__init__(0,0x86, direction=0, notes='Sent to update the current guild status or open the guild buy/sell menu.')

class iMerits(template):
    def __init__(self):
        super().__init__(0,0x8c, direction=0, notes='Contains all merit information. 3 packets are sent.')

class iJobPoints(template):
    def __init__(self):
        super().__init__(0,0x8d, direction=0, notes='Contains all job point information. 12 packets are sent.')

class iPartyMapMarker(template):
    def __init__(self):
        super().__init__(0,0xa0, direction=0, notes='Marks where players are on your map.')

class iSpellList(template):
    def __init__(self):
        super().__init__(0,0xaa, direction=0, notes='Packet that shows the spells that you know.')

class iAbilityList(template):
    def __init__(self):
        super().__init__(0,0xac, direction=0, notes='Packet that shows your current abilities and traits.')

class iMountList(template):
    def __init__(self):
        super().__init__(0,0xae, direction=0, notes='Packet that shows your current mounts.')

class iSeekAnonResp(template):
    def __init__(self):
        super().__init__(0,0xb4, direction=0, notes='Server response sent after you put up party or anon flag.')

class iHelpDeskOPen(template):
    def __init__(self):
        super().__init__(0,0xb5, direction=0, notes='Sent when you open the Help Desk submenu.')

class iReservationResponse(template):
    def __init__(self):
        super().__init__(0,0xbf, direction=0, notes='Sent to inform the client about the status of entry to an instanced area.')

class iPartyStructUPdate(template):
    def __init__(self):
        super().__init__(0,0xc8, direction=0, notes='Updates all party member info in one struct. No player vital data (HP/MP/TP) or names are sent here.')

class iShowEquip(template):
    def __init__(self):
        super().__init__(0,0xc9, direction=0, notes='Shows another player your equipment after using the Check command.')

class iBazaarMessage(template):
    def __init__(self):
        super().__init__(0,0xca, direction=0, notes='Shows another players bazaar message after using the Check command or sets your own on zoning.')

class iLinkshellMessage(template):
    def __init__(self):
        super().__init__(0,0xcc, direction=0, notes='/lsmes text and headers.')

class iFoundItem(template):
    def __init__(self):
        super().__init__(0,0xd2, direction=0, notes='This command shows an item found on defeated mob or from a Treasure Chest.')
        self.fields['_unknown1'] = ulong(0x04)
        self.fields['Dropper'] = ulong(0x08)
        self.fields['Count'] = ulong(0x0c)
        self.fields['Item'] = ushort(0x10)
        self.fields['DropperIdx'] = ushort(0x12)
        self.fields['Idx'] = uint8(0x14)
        self.fields['Old'] = uint8(0x15)
        self.fields['_unknwon4'] = uint8(0x16)
        self.fields['_unknown5'] = uint8(0x17)
        self.fields['Timestamp'] = ulong(0x18)
        self.fields['_unknown96c'] = field(0x1c,92)
        self.fields['_unknown6'] = field(0xac, 28)
        self.fields['_junk1'] = ulong(0x38)

class iLotDropItem(template):
    def __init__(self):
        super().__init__(0,0xd3, direction=0, notes='Sent when someone casts a lot on an item or when the item drops to someone.')
        self.fields['HigherLotter'] = ulong(0x04)
        self.fields['CurrentLotter'] = ulong(0x08)
        self.fields['HighestLotterIdx'] = ushort(0x0c)
        self.fields['HighestLot'] = ushort(0x0e)
        self.fields['CurrentLotterIdx'] = ushort(0x10)
        self.fields['CurrentLot'] = ushort(0x12)
        self.fields['Idx'] = uint8(0x14)
        self.fields['Drop'] = uint8(0x15)
        self.fields['HighestLotterName'] = field(0x16,16)
        self.fields['CurrentLotterName'] = field(0x26, 16)
        self.fields['_junk1'] = field(0x36,6)

class iPartyInvite(template):
    def __init__(self):
        super().__init__(0,0xdc, direction=0, notes='Party Invite packet.')
        self.fields['InviterId'] = ulong(0x04)
        self.fields['Flags'] = ulong(0x08)
        self.fields['InviterName'] = field(0x0c, 16)
        self.fields['_unknown1'] = ushort(0x1c)
        self.fields['_junk1'] = ushort(0x1e)

class iPartyMemberUpdate(template):
    def __init__(self):
        super().__init__(0,0xdd, direction=0, notes='Alliance/party member info - zone, HP%, HP% etc.')
        self.fields['Id'] = ulong(0x04)
        self.fields['HP'] = ulong(0x08)
        self.fields['MP'] = ulong(0x0c)
        self.fields['TP'] = ulong(0x10)
        self.fields['Flags'] = ushort(0x14)
        self.fields['_unknown1'] = ushort(0x16)
        self.fields['Idx'] = ushort(0x18)
        self.fields['_unknown2'] = ushort(0x1a)
        self.fields['_unknown3'] = uint8(0x1c)
        self.fields['Hpp'] = uint8(0x1d)
        self.fields['Mpp'] = uint8(0x1e)
        self.fields['_unknown4'] = uint8(0x1f)
        self.fields['Zone'] = ushort(0x20)
        self.fields['MainJob'] = uint8(0x22)
        self.fields['MainJobLevel'] = uint8(0x23)
        self.fields['SubJob'] = uint8(0x24)
        self.fields['SubJobLevel'] = uint8(0x25)
        self.fields['Name'] = field(0x26,16)

class iCharUpdate(template):
    def __init__(self):
        super().__init__(0,0xdf, direction=0, notes='A packet sent from server which updates character HP, MP and TP.')
        self.fields['Id'] = ulong(0x04)
        self.fields['Hp'] = ulong(0x08)
        self.fields['Mp'] = ulong(0x0c)
        self.fields['Tp'] = ulong(0x10)
        self.fields['Idx'] = ushort(0x14)
        self.fields['Hpp'] = uint8(0x16)
        self.fields['Mpp'] = uint8(0x17)
        self.fields['_unknown1'] = ushort(0x18)
        self.fields['_Unknown2'] = ushort(0x1a)
        self.fields['_unknown3'] = ulong(0x1c)
        self.fields['MainJob'] = uint8(0x20)
        self.fields['MainJobLevel'] = uint8(0x21)
        self.fields['SubJob'] = uint8(0x22)
        self.fields['SubJobLevel'] = uint8(0x23)
        

class iLinkshellEquip(template):
    def __init__(self):
        super().__init__(0,0xe0, direction=0, notes='Updates your linkshell menu with the current linkshell.')
        self.fields['LinkshellNumber'] = uint8(0x04)
        self.fields['InventorySlot'] = uint8(0x05)
        self.fields['_junk1'] = ushort(0x06)
        

class iPartyMemberList(template):
    def __init__(self):
        super().__init__(0,0xe1, direction=0, notes='Sent when you look at the party member list.')
        self.fields['PartyId'] = ushort(0x04)
        self.fields['_unknown1'] = ushort(0x06)

class iCharInfo(template):
    def __init__(self):
        super().__init__(0,0xe2, direction=0, notes='Sends name, HP, HP%, etc.')
        self.fields['Id'] = ulong(0x04)
        self.fields['Hp'] = ulong(0x08)
        self.fields['Mp'] = ulong(0x0c)
        self.fields['Tp'] = ulong(0x10)
        self.fields['_unknown1'] = ulong(0x14)
        self.fields['Idx'] = ushort(0x18)
        self.fields['_unknown2'] = uint8(0x1c)
        self.fields['_unknown3'] = uint8(0x1d)
        self.fields['_unknown4'] = uint8(0x1e)
        self.fields['hpp'] = uint8(0x1f)
        self.fields['mpp'] = uint8(0x20)
        self.fields['_unknown5'] = uint8(0x21)
        self.fields['_unknown6'] = uint8(0x22)
        self.fields['_unknown7'] = uint8(0x23)
        self.fields['Name'] = field(0x24, 16)


class iToggleHeal(template):
    def __init__(self):
        super().__init__(0, 0xe8, direction=0, notes='Toggle heal')
        self.fields['Movement'] = uint8(0x04)
        self.fields['_Unknown2'] = uint8(0x05)
        self.fields['_unknown3'] = uint8(0x06)
        self.fields['_unknown4'] = uint8(0x07)


class iWidescanMob(template):
    def __init__(self):
        super().__init__(0,0xf4, direction=0, notes='Displays one monster.')
        self.fields['Idx'] = ushort(0x04)
        self.fields['Level'] = uint8(0x06)
        self.fields['Type'] = uint8(0x07)
        self.fields['XOffset'] = ushort(0x08)
        self.fields['YOffset'] = ushort(0x0a)
        self.fields['Name'] = field(0x0c, 16)

class iWidescanTrack(template):
    def __init__(self):
        super().__init__(0,0xf5, direction=0, notes='Updates information when tracking a monster.')
        self.fields['X'] = float(0x04)
        self.fields['Z'] = float(0x08)
        self.fields['Y'] = float(0x0c)
        self.fields['Level'] = uint8(0x10)
        self.fields['_padding1'] = uint8(0x11)
        self.fields['Idx'] = ushort(0x12)
        self.fields['Status'] = ulong(0x14)


class iWidescanMark(template):
    def __init__(self):
        super().__init__(0,0xf6, direction=0, notes='Marks the start and ending of a widescan list.')
        self.fields['Type'] = ulong(0x04)
        self.notes = self.notes + '\nPacket indicating start/stop of widescan ?'

class iReraiseActivation(template):
    def __init__(self):
        super().__init__(0,0xf9, direction=0,notes='Reassigns targetable status on reraise activation?')
        self.fields['Id'] = ulong(0x04)
        self.fields['Idx'] = ushort(0x08)
        self.fields['_unknown1'] = uint8(0x0a)
        self.fields['_unknown2'] = uint8(0x0b)

class iFurnitureInteraction(template):
    def __init__(self):
        super().__init__(0,0xfa, direction=0, notes='Confirms furniture manipulation.')
        self.fields['Item'] = ushort(0x04)
        self.fields['_unknown1'] = field(0x06, 6)
        self.fields['SafeSlot'] = uint8(0x0c)
        self.fields['_unknown2'] = field(0x0d, 3)  #shouldnt this be padding?

class iBazaarItemListing(template):
    def __init__(self):
        super().__init__(0,0x105, direction=0, notes='The data that is sent to the client when it is "Downloading data...".')
        self.fields['Price'] = ulong(0x04)
        self.fields['Count'] = ulong(0x08)
        self.fields['_unknown1'] = ushort(0x0c)
        self.fields['Item'] = ushort(0x0e)
        self.fields['InventoryIdx'] = uint8(0x10)  #seller inventoryIdx

class iBazaarSellerInfo(template):
    def __init__(self):
        super().__init__(0,0x106, direction=0, notes='Information on the purchase sent to the buyer when they attempt to buy something.')
        self.fields['Type'] = ulong(0x04)
        self.fields['Name'] = field(0x08, 16)

class iBazaarClosed(template):
    def __init__(self):
        super().__init__(0,0x107, direction=0, notes='Tells you when a bazaar you are currently in has closed.')
        self.fields['Name'] = field(0x04, 16)

class iDataDownload5(template):
    def __init__(self):
        super().__init__(0,0x108, direction=0, notes='The data that is sent to the client when it is "Downloading data...".')
        self.fields['Id'] = ulong(0x04)
        self.fields['Type'] = ulong(0x08)       
        self.fields['_unknown1'] = uint8(0x0c)
        self.fields['_unknown2'] = uint8(0x0d)
        self.fields['Idx'] = ushort(0x0e)
        self.fields['Name'] = field(0x10, 16)

class iBazaarPurchaseInfo(template):
    def __init__(self):
        super().__init__(0,0x109, direction=0, notes='Information on the purchase sent to the buyer when the purchase is successful.')
        self.fields['BuyerId'] = ulong(0x04)
        self.fields['Quantity'] = ulong(0x08)
        self.fields['BuyerIdx'] = ushort(0x0c)
        self.fields['BuyerName'] = field(0x10, 16)
        self.fields['_unknown1'] = ulong(0x20)

class iBazaarBuyerInfo(template):
    def __init__(self):
        super().__init__(0,0x10a, direction=0, notes='Information on the purchase sent to the seller when a sale is successful.')
        self.fields['Quantity'] = ulong(0x04)
        self.fields['ItemId'] = ushort(0x08)
        self.fields['BuyerName'] = field(0x0a, 16)
        self.fields['_unknown1'] = ulong(0x1a)
        self.fields['_unknown2'] = ushort(0x1e)       
        self.notes = self.notes + '\nNeeds to have additional validation, _unknown2 may be variable len & uk1 may not be a long'


class iBazaarOpen(template):
    def __init__(self):
        super().__init__(0,0x10b, direction=0, notes='Bazaar Open Packet: Packet sent when you open your bazaar.')
        self.fields['_unknown1'] = ulong(0x04)
    

class iSparksUpdate(template):
    def __init__(self):
        super().__init__(0,0x110, direction=0, notes='Occurs when you sparks increase and generates the related message.')
        self.fields['SparksTotal'] = ushort(0x04)
        self.fields['_unknown1'] = ushort(0x06)
        self.fields['UnitySharedDesignator'] = uint8(0x08)
        self.fields['UnityPersonDesignator'] = uint8(0x09)
        self.fields['_unknown2'] = field(0x0a, 6)

class iEminenceUpdate(template):
    def __init__(self):
        super().__init__(0,0x111, direction=0, notes='Causes Records of Eminence messages.')
        RoEQIDMask =        int('11111111111100000000000000000000',2)  #32bit, ulong
        RoEQProgressMask =  int('00000000000011111111111111111111',2)  #32bit, ulong
        for i in range(30):
            self.fields['QuestId' + str(i)] = bitField(ulong(0x04 + (i * 4)), RoEQIDMask)
            self.fields['QuestProgress' + str(i)] = bitField(ulong(0x04 + (i * 4)), RoEQProgressMask)
        self.fields['LimitedQuestId'] = bitField(ulong(0x100), RoEQIDMask)
        self.fields['LimitedQuestProgress'] = bitField(ulong(0x100), RoEQProgressMask)

class iRoEQuestLog(template):
    def __init__(self):
        super().__init__(0,0x112, direction=0, notes='Updates your RoE quest log on zone and when appropriate.')
        self.fields['BitfieldData'] = field(0x04, 128)
        self.fields['Order'] = ulong(0x84)

class iCurrencyInfo1(template):
    def __init__(self):
        super().__init__(0, 0x113, direction=0, notes='Contains all currencies to be displayed in the currency menu.')
        self.fields['CP_Sandoria'] = long(0x04)
        self.fields['CP_Bastok'] = long(0x08)
        self.fields['CP_Windurst'] = long(0x0c)
        self.fields['BeastmenSeals'] = ushort(0x10)
        self.fields['KindredSeals'] = ushort(0x12)
        self.fields['KindredCrests'] = ushort(0x14)
        self.fields['HighKindredCrests'] = ushort(0x16)
        self.fields['SacredKindredCrests'] = ushort(0x18)
        self.fields['AncientBeastcoin'] = ushort(0x1a)
        self.fields['ValorPoints'] = ushort(0x1c)
        self.fields['Scylds'] = ushort(0x1e)
        self.fields['GP_Fishing'] = long(0x20)
        self.fields['GP_Woodworking'] = long(0x24)
        self.fields['GP_Smithing'] = long(0x28)
        self.fields['GP_Goldsmithing'] = long(0x2c)
        self.fields['GP_Clothcraft'] = long(0x30)
        self.fields['GP_Leathercraft'] = long(0x34)
        self.fields['GP_Bonecraft'] = long(0x38)
        self.fields['GP_Alchemy'] = long(0x3c)
        self.fields['GP_Cooking'] = long(0x40)
        self.fields['Cinders'] = ulong(0x44)
        self.fields['Fewell_Fire'] = uint8(0x48)
        self.fields['Fewell_Ice'] = uint8(0x49)
        self.fields['Fewell_Wind'] = uint8(0x4a)
        self.fields['Fewell_Earth'] = uint8(0x4b)
        self.fields['Fewell_Lightning'] = uint8(0x4c)
        self.fields['Fewell_Water'] = uint8(0x4d)
        self.fields['Fewell_Light'] = uint8(0x4e)
        self.fields['Fewell_Dark'] = uint8(0x4f)
        self.fields['BallistaPoints' ] = long(0x50)
        self.fields['FelowPoints'] = long(0x54)
        self.fields['Chocobucks_Sandy'] = ushort(0x58)
        self.fields['Chocobucks_Bastok'] = ushort(0x5a)
        self.fields['Chocobucks_Windurst'] = ushort(0x5c)
        self.fields['DailyTally'] = ushort(0x5e)
        self.fields['ResearchMarks'] = long(0x60)
        self.fields['WizenedTunnelWorms'] = uint8(0x64)
        self.fields['WizenedMorionWorms'] = uint8(0x65)
        self.fields['WizenedPhantomWorms'] = uint8(0x66)
        self.fields['_unknown1'] = uint8(0x67)
        self.fields['MoblinMarbles'] = ulong(0x68)
        self.fields['Infamy' ] = ushort(0x6c)
        self.fields['Prestige'] = ushort(0x6e)
        self.fields['LegionPoints'] = long(0x70)
        self.fields['Sparks'] = long(0x74)
        self.fields['ShiningStars'] = long(0x78)
        self.fields['ImperialStanding'] = long(0x7c)
        self.fields['Assault_Leujaoam'] = long(0x80)
        self.fields['Assault_MJTG'] = long(0x84)
        self.fields['Assault_Lebros'] = long(0x88)
        self.fields['Assault_Periqia'] = long(0x8c)
        self.fields['Assault_IlrusiAtoll'] = long(0x90)
        self.fields['NyzulTokens'] = long(0x94)
        self.fields['Zeni'] = long(0x98)
        self.fields['Jettons'] = long(0x9c)
        self.fields['TherionIchor'] = long(0xa0)
        self.fields['AlliedNotes'] = long(0xa4)
        self.fields['AMAN_Vouchers'] = ushort(0xa8)
        self.fields['UnityAccolades'] = ushort(0xaa)
        self.fields['Cruor'] = long(0xac)
        self.fields['ResistanceCredits'] = long(0xb0)
        self.fields['DominionNotes'] = long(0xb4)
        self.fields['5thBattleTrophies'] = uint8(0xb8)
        self.fields['4thBattleTrophies'] = uint8(0xb9)
        self.fields['3rdBattleTrophies'] = uint8(0xba)
        self.fields['2ndBattleTrophies'] = uint8(0xbb)
        self.fields['1stBattleTrophies'] = uint8(0xbc)
        self.fields['CaveConservationPoints'] = uint8(0xbd)
        self.fields['ImperialIDTags'] = uint8(0xbe)
        self.fields['OpCredits'] = uint8(0xbf)
        self.fields['TraverserStones'] = long(0xc0)
        self.fields['Voidstones'] = long(0xc4)
        self.fields['KupofriedConundrums'] = long(0xc8)
        self.fields['MoblinSacks'] = uint8(0xcc)
        self.fields['CrystalStoredFire'] = ushort(0xe8)
        self.fields['CrystalStoredIce'] = ushort(0xea)
        self.fields['CrystalStoredWind'] = ushort(0xec)
        self.fields['CrystalStoredEarth'] = ushort(0xee)
        self.fields['CrystalStoredLightning'] = ushort(0xf0)
        self.fields['CrystalStoredWater'] = ushort(0xf2)
        self.fields['CrystalStoredLight'] = ushort(0xf4)
        self.fields['CrystalStoredDark'] = ushort(0xf6)


class iFishBiteInfo(template):
    def __init__(self):
        super().__init__(0,0x115, direction=0, notes='Contains information about the fish that you hooked.')
        self.fields['_unkonwn1'] = ushort(0x04)
        self.fields['_unknown2'] = ushort(0x06)
        self.fields['_unknown3'] = ushort(0x08)
        self.fields['FishBiteId'] = ulong(0x0a)
        self.fields['_unknown4'] = ushort(0x0e)
        self.fields['_unknown5'] = ushort(0x10)
        self.fields['_unknown6'] = ushort(0x12)
        self.fields['CatchKey'] = ulong(0x14)



class iEqipsetBuildResponse(template):
    def __init__(self):
        super().__init__(0,0x116, direction=0, notes='Returned from the server when building a set.')

class iEquipsetResponse(template):
    def __init__(self):
        super().__init__(0,0x117, direction=0, notes='Returned from the server after the /equipset command.')

class iCurrency2Info(template):
    def __init__(self):
        super().__init__(0,0x118, direction=0, notes='Contains all currencies to be displayed in the currency menu.')
        self.fields['Bayld'] = long(0x04)
        self.fields['KineticUnits'] = ushort(0x08)
        self.fields['CoalitionImprimaturs'] = uint8(0x0a)
        self.fields['_unknown1'] = uint8(0x0b)
        self.fields['ObsidianFragments'] = long(0x0c)
        self.fields['LebondoptWings'] = ushort(0x10)
        self.fields['PulchridoptWings'] = ushort(0x12)
        self.fields['MewyaPlasm'] = long(0x14)
        self.fields['GhastlySTones'] = uint8(0x18)
        self.fields['GhastlyStones+1'] = uint8(0x19)
        self.fields['GhastlyStones+2'] = uint8(0x1a)
        self.fields['VerdigrisStones'] = uint8(0x1b)
        self.fields['VerdigrisStones+1'] = uint8(0x1c)
        self.fields['VerdigrisStones+2'] = uint8(0x1d)
        self.fields['WailingStones'] = uint8(0x1e)
        self.fields['WailingStones+1'] = uint8(0x1f)
        self.fields['WailingStones+2'] = uint8(0x20)
        self.fields['SnowslitStones'] = uint8(0x21)
        self.fields['SnowslitStones+1'] = uint8(0x22)
        self.fields['SnowslitStones+2'] = uint8(0x23)
        self.fields['SnowtipStones'] = uint8(0x24)
        self.fields['SnowtipStones+1'] = uint8(0x25)
        self.fields['SnowtipStones+2'] = uint8(0x26)
        self.fields['SnowdimStones'] = uint8(0x27)
        self.fields['SnowdimStones+1']= uint8(0x28)
        self.fields['SnowdimStones+2'] = uint8(0x29)
        self.fields['SnoworbStones'] = uint8(0x2a)
        self.fields['SnoworbStones+1'] = uint8(0x2b)
        self.fields['SnoworbStones+2'] = uint8(0x2c)
        self.fields['LeafslitStones'] = uint8(0x2d)
        self.fields['LeafslitStones+1'] = uint8(0x2e)
        self.fields['LeafslitStones+2'] = uint8(0x2f)
        self.fields['LeaftipStones'] = uint8(0x30)
        self.fields['LeaftipStones+1'] = uint8(0x31)
        self.fields['LeaftipStones+2'] = uint8(0x32)
        self.fields['LeafdimStones'] = uint8(0x33)
        self.fields['LeafdimStones+1'] = uint8(0x34)
        self.fields['LeafdimStones+2'] = uint8(0x35)
        self.fields['LeaforbStones'] = uint8(0x36)
        self.fields['LeaforbStones+1'] = uint8(0x37)
        self.fields['LeaforbStones+2'] = uint8(0x38)
        self.fields['DuskslitStones'] = uint8(0x39)
        self.fields['DuskslitStones+1']= uint8(0x3a)
        self.fields['DuskslitStones+2'] = uint8(0x3b)
        self.fields['DusktipStones'] = uint8(0x3c)
        self.fields['DusktipStones+1'] = uint8(0x3d)
        self.fields['DusktipStones+2'] = uint8(0x3e)
        self.fields['DuskdimStones'] = uint8(0x3f)
        self.fields['DuskdimStones+1'] = uint8(0x40)
        self.fields['DuskdimStones+2'] = uint8(0x41)
        self.fields['DuskorbStones'] = uint8(0x42)
        self.fields['DuskorbStones+1'] = uint8(0x43)
        self.fields['DuskorbStones+2'] = uint8(0x44)
        self.fields['PellucidStones'] = uint8(0x45)
        self.fields['FernStones'] = uint8(0x46)
        self.fields['TaupeStones'] = uint8(0x47)
        self.fields['_unkonwn2'] = ushort(0x48)
        self.fields['EschaBeads'] = ushort(0x4a)
        self.fields['EschaSilt'] = long(0x4c)
        self.fields['Potpourri'] = ushort(0x50)
        self.fields['_unknown3'] = field(0x52, 0x0e)


class iAbilityRecasts(template):
    def __init__(self):
        super().__init__(0,0x119, direction=0, notes='Contains the currently available job abilities and their remaining recast times.')

class parser(object):
    def __init__(self):
        obj = getTemplateList()
        self.inPackets = {}
        self.outPackets = {}


#windower lua based inbound
inPacket = {}
outPacket = {}
inPacketKnown = {}
outPacketKnown = {}

def getTemplateFilteredList():
    current_module = sys.modules[__name__]
    o2 =  list([cls for name, cls in current_module.__dict__.items() if isinstance(cls, type) and cls.__name__ != 'template' and issubclass(cls, template)])
    instanceList = []
    
    for item in o2:
        i= item()
        delList = []
        for item in i.fields:
            if item.startswith('_'):
                delList.append(item)
        for item in delList:
            del i.fields[item]
        instanceList.append(i)
        if i.direction ==0:
            inPacketKnown[i.typeId] = i
        elif i.direction ==1:
            outPacketKnown[i.typeId] = i
    
    return instanceList

def getTemplateList():
    current_module = sys.modules[__name__]
    o2 =  list([cls for name, cls in current_module.__dict__.items() if isinstance(cls, type) and cls.__name__ != 'template' and issubclass(cls, template)])
    instanceList = []
    for item in o2:
        i= item()
        instanceList.append(i)
        if i.direction ==0:
            inPacket[i.typeId] = i
        elif i.direction ==1:
            outPacket[i.typeId] = i
      
    return instanceList


def getFFXI_SqlTemplateInit():
    current_module = sys.modules[__name__]
    o2 =  list([cls for name, cls in current_module.__dict__.items() if isinstance(cls, type) and cls.__name__ != 'template' and issubclass(cls, template)])
    templateList = []
    for item in o2:
        t = ffxi_sql.packetTemplates()
        templateItem = item()
        t.name = templateItem.name
        t.size = templateItem.size
        t.typeId = templateItem.typeId
        t.src = templateItem.rawReadSource()
        t.notes = templateItem.genNotes()
        t.struct = templateItem.genStruct()
        t.direction = templateItem.direction

        templateList.append(t)
    return templateList


def parseGeneral(pktRecord):
    if not isinstance(pktRecord, ffxi_sql.packetData):
        return None
    else:
        idata = template.iParse(pktRecord.pktPayload)
        if pktRecord.direction ==0:
            if idata[0] not in inPacket:
                inPacket[idata[0]] = template(0,0)
            templ = inPacket[idata[0]]
        elif pktRecord.direction == 1:
            if idata[0] not in outPacket:
                outPacket[idata[0]] = template(0,0)
            templ = outPacket[idata[0]]
        print ('<rowid> %s <Player> %s <PacketType> %s <reportedSize> %s <ActualSize> %s <UsingTemplate> %s <parseMode> %s\n' % (pktRecord.rowid, pktRecord.player.playerName, pktRecord.pktTypeId, pktRecord.pktAshitaSize, len(pktRecord.pktPayload), templ.name, parseMode))
        pprint(templ.getFields(pktRecord.pktPayload))
        return len(templ.fields)

def parseRaw(pktRecord):
    if not isinstance(pktRecord, ffxi_sql.packetData):
        return None
    else:
        idata = template.iParse(pktRecord.pktPayload)
        if pktRecord.direction ==0:
            if idata[0] not in inPacket:
                inPacket[idata[0]] = template(0,0)
            templ = inPacket[idata[0]]
        elif pktRecord.direction == 1:
            if idata[0] not in outPacket:
                outPacket[idata[0]] = template(0,0)
            templ = outPacket[idata[0]]
        forkedTemplate = sys.modules[__name__].__dict__[templ.name]()
        for item in forkedTemplate.fields:
            forkedTemplate.fields[item].postFilter=noFilter

        print ('<rowid> %s <Player> %s <PacketType> %s <reportedSize> %s <ActualSize> %s <UsingTemplate> %s <parseMode> %s\n' % (pktRecord.rowid, pktRecord.player.playerName, pktRecord.pktTypeId, pktRecord.pktAshitaSize, len(pktRecord.pktPayload), templ.name, parseMode))
        pprint(forkedTemplate.getFields(pktRecord.pktPayload))
        return len(templ.fields)

def parseKnownFields(pktRecord):
    if not isinstance(pktRecord, ffxi_sql.packetData):
        return None
    else:
        idata = template.iParse(pktRecord.pktPayload)
        
        if pktRecord.direction ==0:

            if idata[0] not in inPacketKnown:
                inPacketKnown[idata[0]] = template(0,0)
            templ = inPacketKnown[idata[0]]
        elif pktRecord.direction == 1:
            if idata[0] not in outPacketKnown:
                outPacketKnown[idata[0]] = template(0,0)
            templ = outPacketKnown[idata[0]]
        print ('<rowid> %s <Player> %s <PacketType> %s <reportedSize> %s <ActualSize> %s <UsingTemplate> %s <templateSize> %s <parseMode> %s\n' % (pktRecord.rowid, pktRecord.player.playerName, pktRecord.pktTypeId, pktRecord.pktAshitaSize, len(pktRecord.pktPayload), templ.name,0,  parseMode))
        pprint(templ.getFields(pktRecord.pktPayload))
        return len(templ.fields)


def setParseMode(strMode):
    global parseMode
    global pparse

    parseMode = strMode
    if strMode == 'Raw':
        pparse = parseRaw
    elif strMode== 'General':
        pparse = parseGeneral
    elif strMode=='Known':
        pparse = parseKnownFields
    else:
        pparse = parseRaw
        parseMode = strMode + '- defaulting to Raw'

def valParse(pktRecord):
    if not isinstance(pktRecord, ffxi_sql.packetData):
        return None
    else:
        idata = template.iParse(pktRecord.pktPayload)
        if pktRecord.direction == 0:
            if idata[0] not in inPacket:
                inPacket[idata[0]] = template(0,0)
            templ = inPacket[idata[0]]
        elif pktRecord.direction ==1:
            if idata[0] not in outPacket:
                outPacket[idata[0]] = template(0,0)
            templ = outPacket[idata[0]]
        retObj = {}
        for field in templ.fields.keys():
            retObj[field] = templ.fields[field].getValue(pktRecord.pktPayload)
        return retObj

            
#def parseGeneral(pktRecord):
#    if not isinstance(pktRecord, ffxi_sql.packetData):
#        return None
#    else:
#        idata = template.iParse(pktRecord.pktPayload)
#        if pktRecord.direction ==0:
#            if idata[0] not in inPacket:
#                inPacket[idata[0]] = template(0,0)
#            templ = inPacket[idata[0]]
#        elif pktRecord.direction == 1:
#            if idata[0] not in outPacket:
#                outPacket[idata[0]] = template(0,0)
#            templ = outPacket[idata[0]]
#        print ('<rowid> %s <Player> %s <PacketType> %s <reportedSize> %s <ActualSize> %s <UsingTemplate> %s <parseMode> %s\n' % (pktRecord.rowid, pktRecord.player.playerName, pktRecord.pktTypeId, pktRecord.pktAshitaSize, len(pktRecord.pktPayload), templ.name, parseMode))
#        pprint(templ.getFields(pktRecord.pktPayload))
#        return len(templ.fields)



#init stuff
getTemplateList()
getTemplateFilteredList()

parseMode = 'General'
pparse = parseGeneral

