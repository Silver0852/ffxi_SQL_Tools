import os
import bs4
import requests
import ffxi_sql as s
from threading import Thread
from time import sleep
import json
import collections
import datetime
import ast

session = s.cnnf()
#functions to get and parse data
def getByItem(itemId, stack=0):
    #todo determine stack or single 
    if stack== 0:
        response = requests.request('GET','https://www.ffxiah.com/item/%s' % itemId)
    else:
        response = requests.request('GET','https://www.ffxiah.com/item/%s?stack=1' % itemId)
    tx = response.text
    salesIdx = tx.find('Item.sales')
    end = tx[salesIdx:].find(';')
    arrObj = tx[salesIdx:salesIdx+end]
    jsonStr = arrObj[arrObj.find('=')+2:]
    salesList = json.loads(jsonStr)
    soup = bs4.BeautifulSoup(tx,'html.parser')
    stockVal = soup.findAll('table',class_='stdtbl')[0].findAll('tr')[3].findAll('td')[1].getText()
    return s.addSales(salesList, s.cnnf(), itemId, stack), stockVal

def getByPlayer(playerName, serverName='Bahamut'):
    response = requests.request('GET','https://www.ffxiah.com/player/%s/%s' % (serverName,playerName) )
    tx = response.text
    salesIdx = tx.find('Player.sales')
    if salesIdx == -1:
        return False
    end = tx[salesIdx:].find(';')
    arrObj = tx[salesIdx:salesIdx+end]
    jasonStr = arrObj[arrObj.find('=')+2:]
    salesList = json.loads(jasonStr)
    return s.addPlayerSales(salesList, playerName, s.cnnf())


def getGuildPointForSQL(clear=False):
    session = s.cnnf()
    countInDb = session.query(s.gpHistory).filter(s.gpHistory.gpDate==datetime.date.today()).count()
    if countInDb > 0 and clear==False:
        return False
    elif countInDb > 0 and clear:
        session.query(s.gpHistory).filter(s.gpHistory.gpDate==datetime.date.today()).delete()
        session.commit()
    else:
        pass

    response = requests.request('GET',r'https://www.ffxiah.com/guild-pattern')
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table',class_='tbl-gpi')
    rows = table.findAll('tr')
    craftOrder = {0:'Header',1:'Alchemy',2:'Bonecraft',3:'Clothcraft',4:'Cooking',5:'Fishing',6:'Goldsmithing',7:'Leathercraft',8:'Smithing',9:'Woodworking'}
    rankOrder = {1:'Novice',2:'Apprentice',3:'Journeyman',4:'Craftsman',5:'Artisan',6:'Adept',7:'Veteran'}
    rowNum = 1
    for row in rows[1:]:
        colNum = 1
        fields = row.findAll('td')
        for field in fields[1:]:
            gpRec = s.gpHistory()
            gpRec.craft = craftOrder[rowNum]
            gpRec.gpDate = datetime.date.today()
            gpRec.guildRankNum = colNum
            gpRec.guildRank = rankOrder[colNum]
            gpRec.itemid = int(field.find('a').attrs['href'].split('/')[4])
            session.add(gpRec)
            colNum += 1
        rowNum += 1
    session.commit()
    session.close()
    return True

    

def getRecipeById(recipeId):
    #check DB for first match
    #check ffxiah for first match
    #check bgwiki  for first match
    pass

def priceRecipe(recipeId):
    pass

##module operations:: Init
#globalConfig = {}
#session = s.cnnf()

#for configs in session.query(s.ffxiah_scanGlobalConfig).all():
#    globalConfig[configs.configKey] = configs

#def monitor():
#    scanItem = globalConfig['LastScanItemId'].configValue + 1
#    actions = collections.deque()
#    #get ITem scan
#    q = session.query(s.ffxiah_scanObjectConfig).all()
    
##select * from items where flags & 0x40 = 0
##session.query(ffxi_sql.baseItems).filter(ffxi_sql.baseItems.flags.op('&')(0x40) == 0)


##<table class="stdtbl" width="100%">
class config(object):
    def __init__(self):
        self.config = {}
        session = s.cnnf()
        configObj = session.query(s.ffxiah_scanGlobalConfig).all()
        for item in configObj:
            self.config[item.configKey] = item.configValue

    def __getitem__(self, key):
        return self.config.get(key, None)

    def __setitem__(self, key, value):
        session = s.cnnf()
        obj = session.query(s.ffxiah_scanGlobalConfig).filter(key).first()
        obj.configValue = str(value)
        self.config[key] = str(value)
        session.commit()
        

class monitor(object):
    def __init__(self, override=False):
        self.session = s.cnnf()
        self.config = config()
        self.pid = os.getpid()
        if self.config['runningPID'] != '0' and override==False:
            raise 'Already running on <PID> %s' % self.config['runningPID']
        else:
            self.config['runningPID'] = self.pid
        
    def start(self):
        pass


#class monitor(object):
#    class status(object):
#        def __init__(self, monitor):
#            self.status = 'Init'
#            self.runnable = False
#            self.pid = os.getpid()
#            self.monitor = monitor
#            self.processedItems = 0
#            self.processedPlayers = 0
#        def __repr__(self):
#            return '<curStatus> %s <processedItems> %s <processedPlayers> %s' % (self.status, self.processedItems, self.processedPlayers)
            

#    def __init__(self, session=None):
#        self.status = monitor.status()


#        if session is None:
#            self.session = s.cnnf()
#        else:
#            self.session = session
#        session.autocommit = True
#        session.autoflush = True
#        self.monitorPlayers = self.getConfig('monitorPlayers')

#        self.queue = collections.deque()
#        self.prioQueue = collections.deque()
#        prioQ = session.query(s.ffxiah_scanObjectConfig).filter(s.ffxiah_scanObjectConfig.timeSlice==0).all()
#        for item in prioQ:
#            self.prioQueue.append(item)
#        self.status = 'Queued'
#        if self.getConfig('runningPID') == 0:
#            self.status.runnable = True
#            self.setConfig('runningPID', os.getpid())

#    def Process(self):
#        pass

#    def start(self):
#        pass

#    def getConfig(self, configKey):
#        obj = self.session.query(s.ffxiah_scanGlobalConfig).filter(s.ffxiah_scanGlobalConfig.configKey==configKey).first()
#        if obj.dataType == 'List':
#            return ast.literal_eval(obj.keyValue)
#        elif obj.dataType == 'Int':
#            return int(obj.keyValue)
#        else:
#            return obj.keyValue

#    def setConfig(self, configKey, configValue):
#        obj = self.session.query(s.ffxiah_scanGlobalConfig).filter(s.ffxiah_scanGlobalConfig.configKey==configKey).first()
#        obj.configValue =str(configValue)

#    def __repr__(self):
#        return self.status.__repr__()
    