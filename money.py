# Basic WoW money class

class Money:

    def __init__(self, copper=0, silver=0, gold=0):
        self.set(copper+100*silver+10000*gold)

    def set(self, copper):
        self.gold = int(copper / 10000)
        self.silver = int((copper % 10000) / 100)
        self.copper = copper - (self.silver*100) - (self.gold*10000)
        self._copper = copper

    def tuple(self):
        return self.gold, self.silver, self.copper

    def val(self):
        return self._copper

    def gold(self):
        # Converts to gold
        return self._copper / 10000

    def __str__(self):
        return '%sg %ss %sc' % (self.tuple())

    def __cmp__(self, other):
        if type(other) == int or type(other) == long:
            return long(self._copper).__cmp__(long(other))
        return self._copper.__cmp__(other._copper)
