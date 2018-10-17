import datetime
import ffxi_sql as s
import ffxi_packetTemplate as t
import hashlib

processors = {}

class world(object):
    
    player = {}
    zone = {}
    supportStructs = {}
    chatChannels = {}

    def parsePacket(packet):
        dictObj = t.valParse(packet)
        



##world packet bindings
#zoneList = instanced entity array by index
#globals= npc, pc ID last seen mappings

#persist globals to db
#ingored instanced variables i.e. npc spawn status
#manually add some globals state data i.e. npc types and dialogue options per .dats

#pseudo:
#on zone in, persist last state arrays to globals where applicable
#initialize instance arrays
#process next packets
#	next packets update instance arrays by index, creating entries as appropriate
#	create transaction log
