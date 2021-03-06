#!/usr/bin/python
# author: Jan Hybs

import structures
from structures.project_step_measure import ProjectStepMeasure
from structures import pick
from structures.project_step_git import ProjectStepGit
from structures.project_step_container import ProjectStepContainer
from structures.project_step_collect import ProjectStepCollect
from utils.glob import global_configuration


class ProjectStep(object):
    """
    Class representing single step in a project
    :type git:              list[ProjectStepGit]
    :type description:      str
    :type enabled:          bool
    :type verbose:          bool
    :type container:        ProjectStepContainer
    :type repeat:           int
    :type shell:            str
    :type output:           str

    :type variables:        list
    :type measure:          ProjectStepMeasure
    :type collect:          ProjectStepCollect
    """
    def __init__(self, **kwargs):
        self.name = kwargs['name']

        self.git = [ProjectStepGit(**x) for x in kwargs.get('git', [])]
        self.description = kwargs.get('description', [])
        self.enabled = kwargs.get('enabled', True)
        self.verbose = pick(kwargs, False, 'verbose', 'debug')
        self.container = structures.new(kwargs, 'container', ProjectStepContainer)
        self.repeat = kwargs.get('repeat', 1)
        self.shell = kwargs.get('shell', None)
        self.output = kwargs.get(
            'output',
            'stdout' if global_configuration.tty else 'log+stdout'
        )

        # build matrix
        self.variables = kwargs.get('variables', [])

        # artifact generation
        self.measure = structures.new(kwargs, 'measure', ProjectStepMeasure)
        # artifact collection
        self.collect = structures.new(kwargs, 'collect', ProjectStepCollect)
