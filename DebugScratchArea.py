
import ffxi_sql
import ffxi_sql_initData

import os
from pprint import pprint
import datetime
import tksFlags


session = ffxi_sql.cnnf()

#prepBatch
filePath = r'C:\Users\wong1\Desktop\Ashita\plugins\Packets'
fileBase = r'C:\Users\wong1\Desktop\Ashita\plugins'
finishedPath = r'C:\Users\wong1\Desktop\Ashita\plugins\Packets\Processed'

def findFiles(strExt, addExt, condition=lambda x: True):
    for root, dirs, files in os.walk(filePath):
        fileList = []
        for file in files:
            if file.endswith(strExt) and condition(os.path.join(root, file)):
                fileList.append(os.path.join(root, file))
        for file in fileList:
            src = file
            dst = file + addExt
            os.rename(src, dst)

#ffxi_sql_initData.init(session)
def fileModifiedYesterday(filename):
    s = os.stat(filename)
    tsVal = s.st_mtime
    yest = datetime.date.today()- datetime.timedelta(days=1)
    if yest == datetime.date.fromtimestamp(tsVal):
        print('*%s' % filename)
        return True
    else:
        print(filename)
        return False
    

findFiles('.meta','.csv')
findFiles('.meta','.csv', lambda x: True)

i = 0


tList = []

for root, dirs, files in os.walk(filePath):
    for file in files:
        if file[-3:] == 'csv':
            fh =  open(os.path.join(root, file))
            lines = fh.readlines()
            fh.close()
            filehandles = {}
            plr = ffxi_sql.players()
            plr.playerName = '-Undefined'
            for line in lines:
                if not len(line) == 0:
                    fields = line.split(',')
                    if not fields[0] in filehandles:
                        filehandles[fields[0]] = (open(os.path.join(fileBase,fields[0]), 'rb'),ffxi_sql.getFileReference(session, fields[0], fileBase))
                    rec= ffxi_sql.packetData()
                    if fields[0][-3:] == '.in':
                        rec.direction = tksFlags.xiSQL_Enums.FileIO.FILE_IN
                    else:
                        rec.direction = tksFlags.xiSQL_Enums.FileIO.FILE_OUT
                    rec.pktTypeId = int(fields[2])
                    rec.pktAshitaSize = int(fields[3])
                    rec.pktPayload = filehandles[fields[0]][0].read(rec.pktAshitaSize)
                    rec.pktTimeStamp = datetime.datetime.fromtimestamp(int(fields[1]) / (1000 * 1000 * 10))
                    rec.pktOffset = int(fields[5])
                    if plr.playerName != fields[4]:
                        plr = ffxi_sql.getCharacterReference(session, fields[4])
                    rec.player = plr
                    rec.playerId = plr.rowid
                    rec.file = filehandles[fields[0]][1]
                    rec.fileId = filehandles[fields[0]][1].rowid
                    tList.append(rec)#session.add(rec)
                    if i% 1000 == 0:
                        print('<%s: %s> %s/%s: %.2f' % (datetime.datetime.now(),file , i,len(lines), (i/len(lines)) * 100))
                    i+= 1
            print('Processing bulk insert')
            session.bulk_save_objects(tList)
            
            tList.clear()
            print('Committing %i' % i)
            i = 0
            session.commit()

findFiles('.csv','_')

###parse some packet data time::





###import win32pipe, win32file

###p = win32pipe.CreateNamedPipe(r'\\.\pipe\test_pipe',
###    win32pipe.PIPE_ACCESS_DUPLEX,
###    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
###    1, 65536, 65536,300,None)

###win32pipe.ConnectNamedPipe(p, None)  #blocks until receives a connection


###data = "Hello Pipe"  
###win32file.WriteFile(p, data)


###import win32pipe, win32file
###import win32file
###fileHandle = win32file.CreateFile("\\\\.\\pipe\\test_pipe",
###                              win32file.GENERIC_READ | win32file.GENERIC_WRITE,
###                              0, None,
###                              win32file.OPEN_EXISTING,
###                              0, None)
###data = win32file.ReadFile(fileHandle, 4096)
###print data


#-- Automatically generated file: Items
#import ffxiah_tools as t
#import ffxi_sql
#from time import sleep 
#session = ffxi_sql.cnnf()

#dt = session.query(ffxi_sql.baseItems).filter(ffxi_sql.baseItems.flags.op('&')(0x40) == 0).filter(ffxi_sql.baseItems.rowid > 0).all()
#for item in dt[1:]:
#    id = item.rowid
#    t.getByItem(id)
#    print('ItemId: %s' % id)
#    sleep(5)
#    if item.stackSize > 1:
#        t.getByItem(id, 1)
#        print('ItemId-Stack: %s' % id)
#        sleep(5)


#C:\Users\wong1\Desktop\Ashita\addons\findall\data


##########################
#update specific tables, i.e. inventory and playercurrencies, craft & combat skills

#import ffxi_sql as s
#import ffxi_packetTemplate as t
#from hexdump import hexdump as hx
#from pprint import pprint
#session = s.cnnf()

##player list ot update  using accounts 2 & 3

#playerlist = session.query(s.players).filter(s.sa.or_(s.players.accountId==3, s.players.accountId==2)).all()

#ranks = {}
#ranks[0] = 'Amateur'
#ranks[1] = 'Recruit'
#ranks[2] = 'Initiate'
#ranks[3] = 'Novice'
#ranks[4] = 'Apprentice'
#ranks[5] = 'Journeyman'
#ranks[6] = 'Craftsman'
#ranks[7] = 'Artisan'
#ranks[8] = 'Adept'
#ranks[9] = 'Veteran'
#ranks[10] = 'Expert'

#for player in playerlist:
#    #last skills update
#    skillUpdatePkt = session.query(s.packetData).filter(s.sa.and_(s.packetData.direction==0,s.packetData.pktTypeId==0x62, s.packetData.playerId==player.rowid)).order_by(s.sa.desc(s.packetData.pktTimeStamp)).first()
#    skillDict = t.valParse(skillUpdatePkt)


#    cr = s.playerCrafts()
#    cr.playerId = player.rowid
#    cr.alcSkill = skillDict['cAlchemy']
#    cr.alcRank = ranks[skillDict['cAlchemyRank']]
#    cr.boneSkill = skillDict['cBonecraft']
#    cr.boneRank = ranks[skillDict['cBonecraftRank']]
#    cr.clothSkill = skillDict['cClothcraft']
#    cr.clothRank = ranks[skillDict['cClothcraftRank']]
#    cr.cookSkill = skillDict['cCooking']
#    cr.cookRank = ranks[skillDict['cCookingRank']]
#    cr.fishSkill = skillDict['cFishing']
#    cr.fishRank = ranks[skillDict['cFishingRank']]
#    cr.goldSkill = skillDict['cGoldsmithing']
#    cr.goldRank = ranks[skillDict['cGoldsmithingRank']]
#    cr.leatherSkill = skillDict['cLeathercraft']
#    cr.leatherRank = ranks[skillDict['cLeathercraftRank']]
#    cr.smithSkill = skillDict['cSmithing']
#    cr.smithRank = ranks[skillDict['cSmithingRank']]
#    cr.woodSkill = skillDict['cWoodworking']
#    cr.woodRank = ranks[skillDict['cWoodworkingRank']]
#    cr.synergySkill = skillDict['cSynergy']
#    cr.synergyRank = ranks[skillDict['cSynergyRank']]
#    session.add(cr)
#    session.commit()

#################

#update ah sales sortof, more initial load

#import ffxi_sql as s
#import ffxi_packetTemplate as t
#from pprint import pprint
#from hexdump import hexdump as hx
#import datetime

#session = s.cnnf()
#print('start query %s' % datetime.datetime.now())
#sPacketlist = session.query(s.packetData).filter(s.sa.and_(s.packetData.direction==1, s.packetData.pktTypeId==0x96)).all()
#print('finished query %s with %s records' % ( datetime.datetime.now(), len(sPacketlist) ) )
#for item in sPacketlist:
#    dictObj = t.valParse(item)
#    pprint(dictObj)
#    input()

#########################
## initial code set for prompted recipe insertion

#import ffxi_sql as s

#session = s.cnnf()
#icache = session.query(s.baseItems).all()
#data = {}
#for item in icache:
#    data[item.itemName] = item.rowid


#while True:
#    obj = s.recipe()
#    crystalList = {'fire':4096, 'ice':4097,'wind':4098,'earth':4099, 'lightning':4100,'water':4101,'light':4102,'dark':4103 }
    
#    c = input('Crystal: ')
#    while(c not in crystalList):
#        c = input('Try again: ')
#    obj.Crystal = crystalList[c]
#    ingredientList = []
#    t = input('First ingredient: ')
#    ingredientList.append(data[t])
#    while(t != ''):
#        t = input('Additional ingredient: ')
#        if t != '':
#            ingredientList.append(data[t])
#    ki = input('KI requirement: ')
#    ingredientList.sort()
#    t = len(ingredientList)
#    for i in range(8-t):
#        ingredientList.append(0)
#    obj.Ingr1 = ingredientList[0]
#    obj.Ingr2 = ingredientList[1]
#    obj.Ingr3 = ingredientList[2]
#    obj.Ingr4 = ingredientList[3]   
#    obj.Ingr5 = ingredientList[4]
#    obj.ingr6 = ingredientList[5]
#    obj.Ingr7 = ingredientList[6]
#    obj.Ingr8 = ingredientList[7]
    
#    expResultNQ1 = data[input('expected result: ')]
#    expResultNQCount = int(input('expected result count:'))
#    expResultHQ1 = input('HQ1: ')

#initial code for getting list of zones for further inspection, generates rowid ranges from packet data table

#import ffxi_sql as s
#import ffxi_packetTemplate as t

#def getSQL(template):
#    obj = template.fields
#    sqlSelect = []
#    for item in obj:
#        if not item.startswith('_'):
#            fieldType = obj[item]
#            if isinstance(fieldType, t.uint8):
#                sqlSelect.append('dbo.uint8(%s,p.pktPayload) as [%s], \n' % (obj[item].start, item) )
#            elif isinstance(fieldType, t.ushort):
#                sqlSelect.append('dbo.uint16(%s,p.pktPayload) as [%s], \n' % (obj[item].start, item))
#            elif isinstance(fieldType, t.ulong):
#                sqlSelect.append('dbo.uint32(%s, p.pktPayload) as [%s], \n' % (obj[item].start, item))
#            else:
#                sqlSelect.append('substring(p.pktPayload, %s+1, %s) as [%s], \n' % (obj[item].start, obj[item].length, item ))
#    return ''.join( sqlSelect)

#import ffxi_sql as s

#session = s.cnnf()
#dictOjb = session.execute('''select * From vwCrafting;''')
