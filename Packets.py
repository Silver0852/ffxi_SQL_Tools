class packet(object):
    pass

class entityUpdate(packet):
    updateTypeMask = {0x00:'UPDATE_NONE', 0x01:'UPDATE_POS', 0x02:'UPDATE_STATUS', 0x04:'UPDATE_HP', 0x07:'UPDATE_COMBAT', 
                      0x08:'UPDATE_NAME', 0x10:'UPDATE_LOOK', 0x0F:'UPDATE_ALL_MOB', 0x1f:'UPDATE_ALL_CHAR' }

    def __init__(self, buffer):
        pass

