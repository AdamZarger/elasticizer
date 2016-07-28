import argparse
import luigi
import os
import random
from elasticizer import Load
import collections

def buildArgParser():
    parser = argparse.ArgumentParser(prog='elasticizer',
                                     description='from DB to Elasticsearch')

    parser.add_argument('--index', '-i',
                         default=False, required=True, dest='index',
                         help='the Elasticsearch index name that Luigi updates')
    parser.add_argument('--backup', '-b', action='store_true',
                         default=False, required=False, dest='backup',
                         help='create new cycling backup indices with -v1 and -v2 appended and aliased with the index arg')
    parser.add_argument('--table', '-t',
                         default=False, required=True, dest='table',
                         help='the Elasticsearch table name that Luigi reads from')
    parser.add_argument('--mapping_file', '-m',  metavar='mapping file',
                         default='mappings.json', dest='mapping_file',
                         help='the mapping filename used to set up Elasticsearch mappings')
    parser.add_argument('--settings_file', '-s', metavar='settings file',
                         default='settings.json', dest='settings_file',
                         help='the settings filename used to set up Elasticsearch settings')
    parser.add_argument('--docs_file', '-o', 
                         default='tmp.json', dest='docs_file',
                         help='an output file that stores data being loaded into Elasticsearch.')
    parser.add_argument('--restart','-r', action='store_true', 
                        default=False, dest='restart', 
                        help='clear all targets before running')
    parser.add_argument('--clear', action='store_true', 
                        default=False, dest='clear', 
                        help='clear all targets')

    return parser

def clear(last):
    visited, queue = set(), [last]
    while queue:
        task = queue.pop(0)
        if task not in visited:
            visited.add(task)
            queue.extend(luigi.task.flatten(task.requires()))

            if isinstance(task.output(), list):
                pass
            else:
                if task.output().exists():
                    try :
                        task.output().remove()
                    except:
                        pass    

if __name__ == '__main__':
    # get the arguments from the command line
    parser = buildArgParser()
    cmdline_args = parser.parse_args()

    #decide on indexing
    Indexes = collections.namedtuple('Indexes', ['v1', 'v2', 'alias'])
    if cmdline_args.backup:
        indexes = Indexes(v1=cmdline_args.index+'-v1',
                          v2=cmdline_args.index+'-v2',
                          alias=cmdline_args.index)
    else:
        indexes = Indexes(v1=cmdline_args.index,
                          v2=None,
                          alias=None)
    # get the end class
    task = Load(indexes=indexes, 
                mapping_file=cmdline_args.mapping_file,
                settings_file=cmdline_args.settings_file,
                docs_file=cmdline_args.docs_file,
                table=cmdline_args.table)

    if cmdline_args.clear:
        clear(task)

    else:
        if cmdline_args.restart:
            clear(task)

        luigi.build([task], local_scheduler=True)     