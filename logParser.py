import os, sys, json, requests, atexit
from collections import defaultdict
from tkinter import *
from tkinter.ttk import *


class LogParser(object):
    def __init__(self, appdata, path, charListFile):
        self.appdata = appdata
        self.path = path
        self.charListFile = charListFile 
        self.charData = {}
        self.all_abrv = []
        self.kil_abrv = []
        self.surv_abrv = []
        self.lobby_history = {}
        self.recent_players = []
        self.recent_killers = []
        self.lobby = defaultdict(lambda: defaultdict(dict))
        
        self.json2dic()
        self.getAllAbrv()
        self.getPlayers()

    def jsonData(self, filename):
        jsonfile = open(filename, 'r')
        if jsonfile:
            with jsonfile as f:
                data = json.load(f)
        jsonfile.close()
        return data

    def json2dic(self):
        self.charData = self.jsonData(self.charListFile)

    def lines_that_equal(self, line_to_match, fp):
        return [line for line in fp if line == line_to_match]

    def lines_that_contain(self, string, fp):
        return [line for line in fp if string in line]

    def lines_that_start_with(self, string, fp):
        return [line for line in fp if line.startswith(string)]

    def lines_that_end_with(self, string, fp):
        return [line for line in fp if line.endswith(string)]

    def getAllAbrv(self): #get a list of app cosmetic items
        pref = []
        ign_abrv = self.charData['Ignore']
        for root, dirs, files in os.walk(self.path+'\\Steam\\steamapps\\common\\Dead by Daylight\\DeadByDaylight\\Content\\UI\\Icons\\Customization'):
            for file in files:
                fint = '-'.join(file.split('_')[:1])
                if fint not in pref:
                    pref.append(fint)
        pref.sort()
        self.all_abrv = pref
        for key, val in self.charData['Killers'].items():
            self.kil_abrv = self.kil_abrv + val
        for key, val in self.charData['Survivors'].items():
            self.surv_abrv = self.surv_abrv + val

        diff = list(set(self.all_abrv).difference(self.kil_abrv + self.surv_abrv + ign_abrv))
        if diff:
            print ('Error: unidentified item/s' + diff)
            #Unidentefied: iteam needs to be added the Json dict
    
    def getPlayers(self):
        player_str = 'LogOnline: Verbose: Mirrors: [FOnlineSessionMirrors::AddSessionPlayer] Session:GameSession'
        costmetic_str = 'LogCustomization: -->'
        file = open(self.appdata + '\DeadByDaylight\Saved\Logs\DeadByDaylight.log', 'r', encoding="utf8")
        with file as fp:
            for i, line in enumerate(fp):
                if player_str in line:
                    #get players steam id
                    player = line.split("PlayerId:",1)[1].split("|",1)[1].strip()
                    self.recent_players.append(player)
                    #get char's name based on cosmetic by reading the next 7 lines
                    char = []
                    isKiller = False
                    for x in range(0, 6):
                        nxt_ln = next(fp)
                        if costmetic_str in nxt_ln:
                            car_abrv = '-'.join(nxt_ln.split('>')[1:]).strip().split('_')[:1][0]
                            if car_abrv in self.kil_abrv:
                                char = char + [name for name, abrv in self.charData['Killers'].items() if  car_abrv in abrv]
                                isKiller = True
                            elif car_abrv in self.surv_abrv:
                                char = char + [name for name, abrv in self.charData['Survivors'].items() if  car_abrv in abrv]
                    char = list(dict.fromkeys(char))
                    if len(char) == 1:
                        self.lobby_history[player]= char[0]
                        if isKiller:
                            self.recent_killers.append(player)
        file.close()

        # print (self.players[-5:]) # total players in the lobby 
        # print (self.lobby) #lobby wwwwwdictionary 
        # print (self.killers[-1]) #last killer
    def getLobby(self):
        try:
            current_lobby = self.recent_players[-5:]
            last_killer = self.recent_killers[-1] 
        except:
            return
        #add killer to lobby
        
        if last_killer in self.lobby_history.keys():
            self.lobby['Killer'][last_killer]['character'] = self.lobby_history[last_killer]
            try:
                steam = self.getSteam(last_killer)
                self.lobby['Killer'][last_killer]['name'] = steam['name']
                self.lobby['Killer'][last_killer]['url'] = steam['url']
            except:
                self.lobby['Killer'][last_killer]['name'] = ''
                self.lobby['Killer'][last_killer]['url'] = ''

        else:
            self.lobby['Killer'][last_killer]['character'] = 'Unkown'
            self.lobby['Killer'][last_killer]['name'] = 'Unkown'
            self.lobby['Killer'][last_killer]['url'] = 'Unkown'
        #add survivor names to lobby
        for survivor in current_lobby:
            try:
                steam = self.getSteam(survivor)
                steamName = steam['name']
                steamURL = steam['url']
            except:
                steamName = ''
                steamURL = ''
            if (survivor not in self.recent_killers) and (survivor in self.lobby_history.keys()):
                self.lobby['Survivors'][survivor]['character'] = self.lobby_history[survivor]
                self.lobby['Survivors'][survivor]['name'] = steamName
                self.lobby['Survivors'][survivor]['url'] = steamURL
            else:
                try:
                    del self.lobby['Survivors'][survivor]
                except:
                    None

        return self.lobby

    def getSteam(self, steamID):
        proxies = {
            "http": None,
            "https": None,
        } 
        r = requests.post('https://steamid.io/lookup/' + str(steamID), timeout=5,
                            proxies=proxies)

        raw = r.text
        raw = raw.split('<script type="application/ld+json">')[1]
        raw = raw.split(';')[0].strip()
        info = json.loads(raw)
        return info




class App(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.CreateUI()
        #self.LoadTable()
        self.grid(sticky = (N,S,W,E))
        parent.grid_rowconfigure(0, weight = 1)
        parent.grid_columnconfigure(0, weight = 1)

    def CreateUI(self):
        tv = Treeview(self)
        # tv['columns'] = ('role', 'name', 'rank', 'playtime', 'perfect', 't30')
        tv['columns'] = ('role', 'name')
        tv.heading("#0", text='character', anchor='w')
        tv.column("#0", anchor="center", width=100)
        tv.heading('role', text='role')
        tv.column('role', anchor='center', width=100)
        tv.heading('name', text='name')
        tv.column('name', anchor='center', width=100)
        # tv.heading('rank', text='rank')
        # tv.column('rank', anchor='center', width=50)        
        # tv.heading('playtime', text='playtime')
        # tv.column('playtime', anchor='center', width=100)
        # tv.heading('perfect', text='Perfect games')
        # tv.column('perfect', anchor='center', width=100)        
        # tv.heading('t30', text='Top 30')
        # tv.column('t30', anchor='center', width=50)
        tv.grid(sticky = (N,S,W,E))
        self.treeview = tv
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)

    def LoadTable(self):
        self.treeview.insert('', 'end', text="Jake Park", values=('Survivor',
                             'rude','1', '100hr', '500','TRUE'))
    def Delete(self):
        x = self.treeview.get_children()
        for item in x:
            self.treeview.delete(item)



def main():
    def updateUI(UI, x, l):
        UI.Delete()
        x1 = LogParser(xappdata,xpath,xcharListFile)
        if (x.lobby_history == x1.lobby_history):
            print(True)
        else:
            print(False)
            x1.getLobby()
            l = x1.lobby
        x = x1

        kil = l['Killer']
        surv = l['Survivors']
        for each in list(kil.keys()):
            UI.treeview.insert('', 'end', text=kil[each]['character'], values=('Killer', kil[each]['name'],'1', '100hr', '500','TRUE'))
        for each in list(surv.keys()):
            UI.treeview.insert('', 'end', text=surv[each]['character'], values=('Survivor', surv[each]['name'],'1', '100hr', '500','TRUE'))
        root.after(5000, updateUI, UI, x, l)

    def exit_handler():
        #when exiting quickly save json database
        print ('My application is ending!')
    
    xpath = os.path.expandvars(r'%ProgramFiles(x86)%') 
    xappdata = os.path.expandvars(r'%LOCALAPPDATA%')
    xcharListFile = 'charlist.json'
    #------------Initial Log Read-------------------
    x = LogParser(xappdata,xpath,xcharListFile)
    x_l = x.getLobby()
    l = x.lobby
    #---------------------------------------------
    print(x.lobby)
    #--------------UserInterface---------------------
    root = Tk()
    root.title("DBD companion")
    UI = App(root)
    root.after(7000, updateUI, UI, x, l)

    atexit.register(exit_handler)
    root.mainloop()

if __name__ == '__main__':
    main()
    
    
