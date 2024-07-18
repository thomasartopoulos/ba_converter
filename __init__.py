
def classFactory(iface):
    from .mainPlugin import LayerConverter
    return LayerConverter(iface)
