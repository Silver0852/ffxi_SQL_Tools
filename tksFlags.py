import enum
def decodeFlags(enumType, value):
    pass


class xiSQL_Enums(object):
    class FileIO(enum.IntEnum):
        FILE_IN = 0
        FILE_OUT = 1

    class ItemType(enum.IntEnum):
        ITEM_BASIC              = 0x00
        ITEM_GENERAL            = 0x01
        ITEM_USABLE             = 0x02
        ITEM_PUPPET             = 0x04
        ITEM_ARMOR              = 0x08
        ITEM_WEAPON             = 0x10
        ITEM_CURRENCY           = 0x20
        ITEM_FURNISHING         = 0x40
        ITEM_LINKSHELL          = 0x80

    class ItemSubType(enum.IntEnum):
        ITEM_stNORMAL           = 0x00
        ITEM_stLOCKED           = 0x01
        ITEM_stCHARGED          = 0x02
        ITEM_stAUGMENTED        = 0x04
        ITEM_stUNLOCKED         = 0xFE

    class ItemFlags(enum.IntEnum):
        ITEM_FLAG_WALLHANGING   = 0x0001
        ITEM_FLAG_01            = 0x0002
        ITEM_FLAG_02            = 0x0004
        ITEM_FLAG_03            = 0x0008
        ITEM_FLAG_DELIVERYINNER = 0x0010
        ITEM_FLAG_INSCRIBABLE   = 0x0020
        ITEM_FLAG_NOAUCTION     = 0x0040
        ITEM_FLAG_SCROLL        = 0x0080
        ITEM_FLAG_LINKSHELL     = 0x0100
        ITEM_FLAG_CANUSE        = 0x0200
        ITEM_FLAG_CANTRADENPC   = 0x0400
        ITEM_FLAG_CANEQUIP      = 0x0800
        ITEM_FLAG_NOSALE        = 0x1000
        ITEM_FLAG_NODELIVERY    = 0x2000
        ITEM_FLAG_EX            = 0x4000
        ITEM_FLAG_RARE          = 0x8000

    class equipSlot(enum.IntEnum):
        LOC_INVENTORY       = 0
        LOC_MOGSAFE         = 1
        LOC_STORAGE         = 2
        LOC_TEMPITEMS       = 3
        LOC_MOGLOCKER       = 4
        LOC_MOGSATCHEL      = 5
        LOC_MOGSACK         = 6
        LOC_MOGCASE         = 7
        LOC_WARDROBE        = 8
        LOC_MOGSAFE2        = 9
        LOC_WARDROBE2       = 10
        LOC_WARDROBE3       = 11
        LOC_WARDROBE4       = 12

    

    
# notes: use VV< RR< Apoc on thf
#todo: Create itemattribute table, rowid, itemid, attributeId, value
#todo: create attribute table, rowid, attribute text
#todo: create table known itemFiles rowid, path, file, updateDate
#todo: Create item class for finer tuned organization.- create UI element for maintenance in game
#todo: create notes table and notes type table: notes { rowid, noteType, noteText }
#todo: create item type table as:
            #enum class ItemType : uint32_t {
            #    None = 0x0000,
            #    Item = 0x0001,
            #    QuestItem = 0x0002,
            #    Fish = 0x0003,
            #    Weapon = 0x0004,
            #    Armor = 0x0005,
            #    Linkshell = 0x0006,
            #    UsableItem = 0x0007,
            #    Crystal = 0x0008,
            #    Currency = 0x0009,
            #    Furnishing = 0x000A,
            #    Plant = 0x000B,
            #    Flowerpot = 0x000C,
            #    PuppetItem = 0x000D,
            #    Mannequin = 0x000E,
            #    Book = 0x000F,
            #    RacingForm = 0x0010,
            #    BettingSlip = 0x0011,
            #    SoulPlate = 0x0012,
            #    Reflector = 0x0013,
            #    Logs = 0x0014,
            #    LotteryTicket = 0x0015,
            #    TabulaM = 0x0016,
            #    TabulaR = 0x0017,
            #    Voucher = 0x0018,
            #    Rune = 0x0019,
            #    Evolith = 0x001A,
            #    StorageSlip = 0x001B,
            #    Type1 = 0x001C
            #};

