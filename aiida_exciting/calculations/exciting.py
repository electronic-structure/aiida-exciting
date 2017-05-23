# -*- coding: utf-8 -*-
"""
Plugin to create an Exciting input file.
"""
import os

from aiida.orm.calculation.job import JobCalculation
from aiida.orm.data.array.kpoints import KpointsData
from aiida.orm.data.structure import StructureData
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.remote import RemoteData
from aiida_exciting.data.lapwbasis import LapwbasisData
from aiida.common.utils import classproperty
from aiida.common.datastructures import CalcInfo
from aiida.common.datastructures import CodeInfo
__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi"

class ExcitingCalculation(JobCalculation):
    """
    Exciting FP-LAPW code
    For more information, refer to http://exciting-code.org/
    """

    _OUTPUT_FILE_NAME = 'aiida.out'

    def _init_internal_params(self):
        super(ExcitingCalculation, self)._init_internal_params()

        self._default_parser = 'exciting.output'

        self._DEFAULT_OUTPUT_FILE = self._OUTPUT_FILE_NAME

    def _prepare_for_submission(self, tempfolder, inputdict):

        settings = inputdict.pop(self.get_linkname('settings'), None)
        if settings is None:
            settings_dict = {}
        else:
            if not isinstance(settings, ParameterData):
                raise InputValidationError("settings, if specified, must be of "
                                           "type ParameterData")
            settings_dict = settings.get_dict()

        try:
            code = inputdict.pop(self.get_linkname('code'))
        except KeyError:
            raise InputValidationError("No code specified for this calculation")

        try:
            parameters = inputdict.pop(self.get_linkname('parameters'))
        except KeyError:
            raise InputValidationError("No parameters specified for this calculation")
        if not isinstance(parameters, ParameterData):
            raise InputValidationError("parameters is not of type ParameterData")

        calcinfo = CalcInfo()

        calcinfo.uuid = self.uuid
        # Empty command line by default
        cmdline_params = settings_dict.pop('CMDLINE', [])

        #calcinfo.stdin_name = self._INPUT_FILE_NAME
        #calcinfo.stdout_name = self._OUTPUT_FILE_NAME

        codeinfo = CodeInfo()
        codeinfo.cmdline_params = list(cmdline_params)
        ##calcinfo.stdin_name = self._INPUT_FILE_NAME
        codeinfo.stdout_name = self._OUTPUT_FILE_NAME
        codeinfo.code_uuid = code.uuid
        calcinfo.codes_info = [codeinfo]
        #
        #calcinfo.remote_copy_list = remote_copy_list
        #calcinfo.remote_symlink_list = remote_symlink_list

        calcinfo.local_copy_list = []

        # Retrieve by default the output file and the xml file
        calcinfo.retrieve_list = []
        calcinfo.retrieve_list.append(self._OUTPUT_FILE_NAME)
        calcinfo.retrieve_list.append("info.xml")
        #calcinfo.retrieve_list.append(self._DATAFILE_XML)
        #settings_retrieve_list = settings_dict.pop('ADDITIONAL_RETRIEVE_LIST', [])

        try:
            structure = inputdict.pop(self.get_linkname('structure'))
        except KeyError:
            raise InputValidationError("No structure specified for this calculation")
        if not isinstance(structure, StructureData):
            raise InputValidationError("structure is not of type StructureData")

        try:
            kpoints = inputdict.pop(self.get_linkname('kpoints'))
        except KeyError:
            raise InputValidationError("No kpoints specified for this calculation")
        if not isinstance(kpoints, KpointsData):
            raise InputValidationError("kpoints is not of type KpointsData")

        kmesh, koffset = kpoints.get_kpoints_mesh()
        
        lapw_basis_list = {}
        for link in inputdict.keys():
            if link.startswith("lapwbasis_"):
                kindstring = link[len("lapwbasis_"):]
                lapw_basis_list[kindstring] = inputdict.pop(link)

        import xml.etree.ElementTree as ET
        root = ET.Element("input")
        ET.SubElement(root, "title").text = "input file created with AiiDA"
        struct = ET.SubElement(root, "structure", attrib={'speciespath' : './', 'autormt' : 'true'})
        cryst = ET.SubElement(struct, "crystal", attrib={'scale' : '1.889725989'})

        from numpy import matrix
        lat_vec = matrix(structure.cell)
        inv_lat_vec = lat_vec.T.I;

        for vector in structure.cell:
            ET.SubElement(cryst, "basevect").text = " ".join(['%18.10f'%e for e in vector])

        for kind in structure.kinds:
            lapw_basis = lapw_basis_list[kind.symbol]
            calcinfo.local_copy_list.append((lapw_basis.get_file_abs_path(), lapw_basis.filename))

            s = ET.SubElement(struct, "species", attrib={'speciesfile' : lapw_basis.filename})
            for site in structure.sites:
                if site.kind_name == kind.name:
                    pos_cart = matrix(site.position)
                    pos_lat = inv_lat_vec * pos_cart.T
                    ET.SubElement(s, "atom", attrib={'coord' : " ".join(['%18.10f'%e for e in pos_lat])})
       
        parameters_dict = parameters.get_dict()
        groundstate_attrib = {}
        if 'groundstate' in parameters_dict:
            groundstate_attrib = parameters_dict['groundstate']
        groundstate_attrib['ngridk'] = " ".join(['%i'%e for e in kmesh])
        ET.SubElement(root, "groundstate", attrib=groundstate_attrib)

        tree = ET.ElementTree(root)
        tree.write(tempfolder.get_abs_path("input.xml"))

        return calcinfo

    def use_lapwbasis_from_family(self, family_name):
        from collections import defaultdict

        try:
            structure = self.get_inputs_dict()[self.get_linkname('structure')]
        except AttributeError:
            raise ValueError("Structure is not set yet! Therefore, the method "
                             "use_lapwbasis_from_family cannot automatically set "
                             "the LAPW basis")

        from aiida.orm import Group
        lapwbasis_group = Group.get(family_name, type_string=LapwbasisData.lapwbasisfamily_type_string)
        
        lapwbasis_list = {}
        for node in lapwbasis_group.nodes:
            if isinstance(node, LapwbasisData):
                lapwbasis_list[node.chemical_symbol] = node

        for kind in structure.kinds:
            symbol = kind.symbol
            self.use_lapwbasis(lapwbasis_list[symbol], symbol)

    @classmethod
    def _get_linkname_lapwbasis(cls, kind):
        # If it is a list of strings, and not a single string: join them
        # by underscore
        if isinstance(kind, (tuple, list)):
            suffix_string = "_".join(kind)
        elif isinstance(kind, basestring):
            suffix_string = kind
        else:
            raise TypeError("The parameter 'kind' of _get_linkname_lapwbasis can "
                            "only be a string or a list of strings")

        return "lapwbasis_%s"%suffix_string

    @classproperty
    def _use_methods(cls):
        """
        Extend the parent _use_methods with further keys.
        """
        tmp = { 
            "structure": {
                'valid_types': StructureData,
                'additional_parameter': None,
                'linkname': 'structure',
                'docstring': "Choose the input structure to use",
            },
            "settings": {
                'valid_types': ParameterData,
                'additional_parameter': None,
                'linkname': 'settings',
                'docstring': "Use an additional node for special settings",
            },
            "parameters": {
                'valid_types': ParameterData,
                'additional_parameter': None,
                'linkname': 'parameters',
                'docstring': ("Use a node that specifies the input parameters "
                              "for the namelists"),
            },
            "parent_folder": {
                'valid_types': RemoteData,
                'additional_parameter': None,
                'linkname': 'parent_calc_folder',
                'docstring': ("Use a remote folder as parent folder (for "
                              "restarts and similar"),
            },
            "lapwbasis": {
                'valid_types': LapwbasisData,
                'additional_parameter': "kind",
                'linkname': cls._get_linkname_lapwbasis,
                'docstring': ("Use a node for the LAPW specis file of one of "
                              "the elements in the structure. You have to pass "
                              "an additional parameter ('kind') specifying the "
                              "name of the structure kind (i.e., the name of "
                              "the species) for which you want to use this "
                              "file. You can pass either a string, or a "
                              "list of strings if more than one kind uses the "
                              "same species"),
            },
            "kpoints" : {
                'valid_types': KpointsData,
                'additional_parameter': None,
                'linkname': 'kpoints',
                'docstring': "Use the node defining the kpoint sampling to use"
            }
        }

        retdict = JobCalculation._use_methods
        retdict.update(tmp)

        return retdict

