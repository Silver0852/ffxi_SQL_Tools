import datetime
import tksFlags
import ffxiah_tools as ah
import genFFXI_SQL_Tools as g
import ffxi_sql
s = ffxi_sql
import argparse
import os

parser = argparse.ArgumentParser(description='FFXI CLI tools for managing the local xi db and XI char instance communications')
parser.add_argument('-l', '--loadFile', help='specify a packet dump to load into ffxisql')
parser.add_argument('-f','--fixold', help='modify metadata to fix old packet capture style of hardcoded file resolution on my surface', action='store_true')
parser.add_argument('-v', '--verbose', help='log to std out', action='count', default=0)
parser.add_argument('-p', '--ahPlayer', help='get ffxiah sales for player name')
parser.add_argument('-P', '--ahPlayerId', help='get ffxiah sales for player ID', type=int)
parser.add_argument('-i', '--ahItem', help='get ffxiah sales for item name')
parser.add_argument('-I', '--ahItemId', help='get ffxiah sales for item ID', type=int)
parser.add_argument('-m','--getMonitoredPlayers', help='get ffxiah sales for monitored playres', action='store_true')
args = parser.parse_args()

if args.ahItemId is not None and args.ahItem is not None:
    raise Exception('Argument error, mutually exclusive args -I %d -i %s' % (args.ahItemId, args.ahItem ))

if args.ahPlayerId is not None and args.ahPlayer is not None:
    raise Exception('Argument error, mutually exclusive args -P %d -p %s' % (args.ahPlyaerId, args.ahPlayer))

if args.ahItem is not None:
    print('dostuff for ahItem by name')

if args.ahItemId:
    print('do stuff for ahitemid')

if args.ahPlayerId is not None:
    print('dostuff for ah player ID')

if args.ahPlayer is not None:
    g.ah.getByPlayer(args.ahPlayer)

if args.getMonitoredPlayers:
    print('ahtools.justdostuff')





if args.loadFile is not None:
    i = 0
    tList = []
    session = s.cnnf()
    if not os.path.exists(args.loadFile):
        raise Exception('Argument error, file not found: %s' % args.loadFile)
    fh = open(args.loadFile, 'r')
    #sanity checks
    szMetafile = os.stat(args.loadFile).st_size
    textData = fh.read()
    fh.close()
    filehandles = {}
    plr = s.players()
    plr.playerName = '-Undefined'
    lineData = textData.split('\n')
    packetMetrics = {}
    packetMetrics['records'] = len(lineData)
    for line in lineData:
        if not len(line) == 0:
            fields = line.split(',')
            if not fields[0] in filehandles:
                fn = fields[0].split('\\')[-1]
                filehandles[fields[0]]= (open('./' + fn, 'rb'), s.getFileReference(session, fn, None))
            rec= ffxi_sql.packetData()
            if fields[0][-3:] == '.in':
                rec.direction = 0
            else:
                rec.direction = 1
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
            tList.append(rec)
            if i % 1000 ==0:
                print('<%s: %s> %s/%s: %.2f' % (datetime.datetime.now(),args.loadFile , i,len(lineData), (i/len(lineData)) * 100))
            i += 1
    print('processing bulk insert %d' % i)
    session.bulk_save_objects(tList)
    print('calling commit')
    session.commit()
