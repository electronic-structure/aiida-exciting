ha2ev = 27.21138505
au2angs = 0.5291772108

def parse_xml_output(filename):
    import xml.etree.ElementTree as ET
    tree = ET.parse(filename)
    root = tree.getroot()

    node = root.findall('./groundstate')[0]
    if node.attrib.get('status', '') != 'finished':
        return False, {}
        
    # count number of iterations
    niter = len(root.findall('./groundstate/scl/iter'))

    # get node with last iteration
    node_iter = root.findall("./groundstate/scl/iter[@iteration='%i']"%niter)[0]
    node = root.findall("./groundstate/scl/iter[@iteration='%i']/energies"%niter)[0]
    node_cryst = root.findall("./groundstate/scl/structure/crystal")[0]
    
    res = {}
    res['energy'] = float(node.attrib['totalEnergy']) * ha2ev
    res['energy_accuracy'] = float(node_iter.attrib['deltae']) * ha2ev
    res['energy_units'] = 'eV'
    res['energy_accuracy_units'] = 'eV'
    res['volume'] = float(node_cryst.attrib['unitCellVolume']) * (au2angs**3)
    res['volume_units'] = 'angstrom^3'

    return True, res

if __name__ == '__main__':
    status, res = parse_xml_output('info.xml')
    print res
