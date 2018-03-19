# -*- coding: utf-8 -*-
import unittest
import os  # noqa: F401
import json  # noqa: F401
import time
import shutil
import requests

from os import environ
try:
    from ConfigParser import ConfigParser  # py2
except:
    from configparser import ConfigParser  # py3

from pprint import pprint  # noqa: F401

from biokbase.workspace.client import Workspace as workspaceService
from landContigFilter.landContigFilterImpl import landContigFilter
from landContigFilter.landContigFilterServer import MethodContext
from landContigFilter.authclient import KBaseAuth as _KBaseAuth

from AssemblyUtil.AssemblyUtilClient import AssemblyUtil

class landContigFilterTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = environ.get('KB_AUTH_TOKEN', None)
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('landContigFilter'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'landContigFilter',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.wsClient = workspaceService(cls.wsURL)
        cls.serviceImpl = landContigFilter(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']
 
        cls.test_filename = '92477.assembled.fna'
        cls.test_filename = 'test.fna'

        cls.test_path = os.path.join(cls.scratch,
                                          cls.test_filename)
        shutil.copy(os.path.join("data", 
                                 cls.test_filename), cls.test_path)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.wsClient.delete_workspace({'workspace': cls.wsName})
            print('Test workspace was deleted')

    def getWsClient(self):
        return self.__class__.wsClient

    def getWsName(self):
        if hasattr(self.__class__, 'wsName'):
            return self.__class__.wsName
        suffix = int(time.time() * 1000)
        wsName = "test_landContigFilter_" + str(suffix)
        ret = self.getWsClient().create_workspace({'workspace': wsName})  # noqa
        self.__class__.wsName = wsName
        return wsName

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    def load_fasta_file(self, filename, obj_name, contents):
        f = open(filename, 'w')
        f.write(contents)
        f.close()
        assemblyUtil = AssemblyUtil(self.callback_url)
        assembly_ref = assemblyUtil.save_assembly_from_fasta({'file': {'path': filename},
                                                              'workspace_name': self.getWsName(),
                                                              'assembly_name': obj_name
                                                              })
        return assembly_ref

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    def get_fasta_file(self, filename, obj_name):
        assemblyUtil = AssemblyUtil(self.callback_url)
        assembly_ref = assemblyUtil.save_assembly_from_fasta({'file': {'path': filename},
                                                              'workspace_name': self.getWsName(),
                                                              'assembly_name': obj_name
                                                              })
        return assembly_ref

    def my_filter_contigs_max_ok(self):

        assembly_ref = self.get_fasta_file(self.test_path,
                                             'TestAssembly2')

        # Second, call your implementation
        ret = self.getImpl().filter_contigs_max(self.getContext(),
                                            {'workspace_name': self.getWsName(),
                                             'assembly_input_ref': assembly_ref,
                                             'min_length': 1,
                                             'max_length': 20000
                                             })

        # Validate the returned data
        print "******test_filter_contigs_max_ok"
        self.assertEqual(ret[0]['n_initial_contigs'], 72)
        self.assertEqual(ret[0]['n_contigs_removed'], 39)
        self.assertEqual(ret[0]['n_contigs_remaining'], 33)

    def test_assembly_metadata(self):

        assembly_ref = self.get_fasta_file(self.test_path,
                                             'TestAssembly3')
        print "ASSEMBLY_REF=", assembly_ref

        # Second, call your implementation
        ret = self.getImpl().assembly_metadata_report(self.getContext(),
                                            {'workspace_name': self.getWsName(),
                                             'assembly_input_ref': assembly_ref,
                                             'showContigs': 1
                                             })

        # Validate the returned data
        print  ret
