class TopMenuItem():
    header = "Header"
    id = "header"
    classes = ''
    weight = 99

    def __init__(self, header, id, classes, weight):
        self.header = header
        self.id = id
        self.classes = classes
        self.weight = weight

    def __lt__(self, other):
         return self.weight < other.weight


class TopMenu():
    menu_items = []

    def addItem(self, item):
        self.menu_items.append(item)

    def getMenuItems(self):
        self.menu_items.sort()
        return self.menu_items

    def clearItems(self):
        del self.menu_items[:]

def getTopMenu(selected):
    top_menu = TopMenu()

    top_menu.clearItems()

    if(len(top_menu.getMenuItems()) < 1):
        top_menu.addItem(TopMenuItem('Logout','user_logout','', 99))

        classes = ''

        if('home' == selected ):
            classes = 'current'

        top_menu.addItem(TopMenuItem('Home','home',classes, 1))

    return top_menu.getMenuItems()

def getPlayerProfileItems():
    items = list()

    profile = { 'classes': '', 'url' : 'user_profile', 'header' : 'Profile' }
    logout = { 'classes' : '', 'url' : 'user_logout', 'header' : 'Logout' }

    items.append(profile)
    items.append(logout)

    return items
