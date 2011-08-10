# Basic WoW money class

class Money:

    def __init__(self, copper):
        self.set(copper)

    def set(self, copper):
        self.gold = int(copper / 10000)
        self.silver = int((copper % 10000) / 100)
        self.copper = copper - (self.silver*100) - (self.gold*10000)
        self._copper = copper

    def tuple(self):
        return self.gold, self.silver, self.copper

    def gold(self):
        # Converts to gold
        return self._copper / 10000

    def __str__(self):
        return '%sg %ss %sc' % (self.tuple())
