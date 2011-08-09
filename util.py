
def money(copper):
    gold = int(copper / 10000)
    silver = int((copper % 10000) / 100)
    copper = copper - (silver*100) - (gold*10000)
    return gold, silver, copper
