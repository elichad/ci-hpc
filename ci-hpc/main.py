#!/usr/bin/python3
# author: Jan Hybs


# lustre/sw/anaconda/anaconda3/bin/python3
# module load anaconda/python3
# module load singularity/2.4
# module load python-3.6.3-gcc-6.2.0-snvgj45
# bin/python


import argparse
import os
import sys
import time
import subprocess
from collections import defaultdict

import utils.strings
from utils.glob import global_configuration


def parse_args():
    from utils.parsing import RawFormatter

    # create parser
    parser = argparse.ArgumentParser(formatter_class=RawFormatter)
    parser.add_argument('--project', type=str, required=True, help='''R|
                            Name of the project.
                            Based on this value, proper configuration will be
                            loaded (assuming --config-dir) was not set.
                            ''')
    parser.add_argument('--git-url', type=str, default=None, help='''R|
                            URL of the git repository. It has no usage for now but 
                            it is planned in the future, where configuration may be
                            part of the repository
                            ''')
    parser.add_argument('--git-commit', action='append', type=str, default=[], help='''R|
                            SHA of the commit to work with.
                            If no value is provided, will be checkout out to the
                            last commit.
                            ''')
    parser.add_argument('--git-branch', action='append', type=str, default=[], help='''R|
                            Name of the branch to check out.
                            If --git-commit is given, resulting git HEAD
                            will be renamed to this value.
                                This is useful when running commits from the past
                                (there will be no detached state nor branch HEAD.)

                            Default value is "master" ''')
    parser.add_argument('--config-dir', type=str, default=None, help='''R|
                            Path to the directory, where config.yaml (and optionally
                            variables.yaml) file is/are located. If no value is set
                            default value will cfg/<project>,
                            where <project> is name of the project given.
                            ''')
    parser.add_argument('--execute', choices=['local', 'pbs'], default=None, help='''R|
                            If set, will generate bash file where it calls itself 
                            once again, but without --generate flag.
                            ''')
    parser.add_argument('--timeout', '-t', type=int, default=0, help='''R|
                            If --execute is pbs (or any value besides local) will wait for the job to finish.
                            By default there is no timeout. Specify in seconds.
                            ''')
    parser.add_argument('--check-interval', type=int, default=5, help='''R|
                            If --execute is pbs (or any value besides local) will wait for the job to finish.
                            Interval, in which the script quiries the HPC for the job status.
                            Specify in seconds.
                            ''')
    parser.add_argument('--log-path', type=str, default=None, help='''R|
                            If set, will override standard log file location
                            ''')
    parser.add_argument('-v', '--verbosity', default=0, action='count', help='''R|
                            Increases verbosity of the application.
                            ''')
    parser.add_argument('step', type=str, nargs='*', default=['install', 'test'])

    # parse given arguments
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    # override log_path if set before actually creating logger
    if args.log_path:
        global_configuration.log_path = args.log_path

    # -------------------------------------------------------

    # now import other packages
    import utils.config as cfgutil
    from utils.logging import logger
    from utils.config import Config as cfg
    from utils.strings import generate_random_key as rands, pad_lines

    from proc.project import ProcessProject
    from structures.project import Project
    import colorama

    colorama.init()

    __root__ = global_configuration.root
    __cfg__ = global_configuration.cfg
    __src__ = global_configuration.src

    # change stream_handler level to info
    logger.set_level('INFO', logger.LOGGER_STREAMHANDLER)
    logger.increase_verbosity(args.verbosity)

    logger.debug('app args: %s', str(args), skip_format=True)

    # convert list ["key:value", "key2:value2", ...] to dict {key:value, key2:value2}
    # default value for this dictionary is string value 'master'
    args.git_branch = dict(tuple(d.split(':', 1)) for d in args.git_branch)
    args.git_branch = defaultdict(lambda: 'master', **args.git_branch)

    # default value for this dictionary is string value ''
    args.git_commit = dict(tuple(d.split(':', 1)) for d in args.git_commit)
    args.git_commit = defaultdict(lambda: '', **args.git_commit)

    # all the paths depend on the project name
    project_name = args.project
    
    # all configuration files are cfg/<project-name> directory if not set otherwise
    project_dir = args.config_dir if args.config_dir else os.path.join(__cfg__, project_name)
    if args.config_dir:
        if not os.path.exists(args.config_dir):
            logger.warning('invalid config location given: %s', project_dir)
            project_dir = os.path.join(__cfg__, project_name)
            logger.warning('will try to use %s instead', project_dir)
            
    if not os.path.exists(project_dir):
        logger.error('no valid configuration found for the project %s', project_name)
        sys.exit(1)

    # execute on demand using pbs/local or other system
    if args.execute:
        project_execute_path = os.path.join(project_dir, 'execute.sh')
        if os.path.exists(project_execute_path):
            with open(project_execute_path, 'r') as fp:
                project_execute_script = fp.read()
        else:
            project_execute_script = '\n'.join([
                '#!/bin/bash --login',
                'echo "<ci-hpc-install>"',
                '<ci-hpc-install>',
                'echo "<ci-hpc-exec>"',
                '<ci-hpc-exec>',
                'exit $?',
            ])

        install_args = [os.path.join(__root__, 'share', 'install.sh')]
        name = 'tmp.entrypoint-%d-%s.sh' % (time.time(), rands(6))
        bash_path = os.path.join(__root__, 'tmp', name)
        logger.debug('Generating script %s', bash_path)

        with open(bash_path, 'w') as fp:
            exec_args = [
                sys.executable,
                os.path.join(__src__, 'main.py'),
                ' '.join(args.step),
            ]
            for arg in ['project', 'git_url', 'config_dir']:
                value = getattr(args, arg)
                if value:
                    exec_args.append('--%s=%s' % (arg.replace('_', '-'), str(value)))
            for arg in ['git_branch', 'git_commit']:
                value = getattr(args, arg)
                for k, v in value.items():
                    exec_args.append('--%s=%s:%s' % (arg.replace('_', '-'), k, v))
            fp.write(
                cfgutil.configure_string(project_execute_script, {
                    'ci-hpc-exec': ' '.join(exec_args),
                    'ci-hpc-install': ' '.join(install_args),
                    'ci-hpc-exec-no-interpret': ' '.join(exec_args[1:]),
                }))
        os.chmod(bash_path, 0o777)
        logger.debug('ci-hpc-exec set to %s', ' '.join(exec_args), skip_format=True)

        # execute on demand using specific system (local/pbs for now)
        logger.info('executing script %s using %s system', bash_path, args.execute)
        if args.execute == 'local':
            p = subprocess.Popen([bash_path])

            # def cleanup():
            #     logger.info('CLEANING PROCESSES')
            #     os.killpg(0, signal.SIGKILL)
            # atexit.register(cleanup)

            p.wait()

        elif args.execute == 'pbs':
            logger.debug('running cmd: %s', str(['qsub', bash_path]), skip_format=True)

            qsub_output = str(subprocess.check_output(['qsub', bash_path]).decode()).strip()
            cmd = [
                sys.executable,
                os.path.join(__src__, 'wait_for.py'),
                qsub_output,
                '--timeout=%d' % args.timeout,
                '--check-interval=%d' % args.check_interval,
                '--live-log=%s' % global_configuration.log_path,
                '--quiet',
            ]
            logger.info('waiting for job (%s) to finish', qsub_output)
            subprocess.Popen(cmd).wait()
        os.unlink(bash_path)
        sys.exit(0)

    if global_configuration.tty:
        logger.info('Started ci-hpc in a %s mode',
                    colorama.Back.BLUE +
                    colorama.Fore.CYAN +
                    colorama.Style.BRIGHT +
                    ' tty '
                    + colorama.Style.RESET_ALL)
    else:
        logger.info('Started ci-hpc *not* in a tty mode')

    # this file contains only variables which can be used in config.yaml
    variables_path = os.path.join(project_dir, 'variables.yaml')
    # this file contains all the sections and steps for installation and testing
    config_path = os.path.join(project_dir, 'config.yaml')
    
    # update cpu count
    variables = cfgutil.load_config(variables_path)
    # variables['cpu-count'] = args.cpu_count

    # load config
    project_config = cfgutil.configure_file(config_path, variables)
    logger.debug('yaml configuration: \n%s', pad_lines(utils.strings.to_yaml(project_config)), skip_format=True)

    # specify some useful global arguments which will be available in the config file
    global_args_extra = {
        'project-name': project_name,
        'project-dir': project_dir,
        'arg': dict(
            branch=defaultdict(lambda: 'master', **dict(args.git_branch)),
            commit=defaultdict(lambda: '', **dict(args.git_commit)),
        )
    }

    # parse config
    project_definition = Project(project_name, **project_config)
    project_definition.update_global_args(global_args_extra)

    project = ProcessProject(project_definition)
    logger.info('processing project %s, section %s', project_name, args.step)

    # -----------------------------------------------------------------

    if 'install' in args.step:
        project.process_section(project_definition.install)

    if 'test' in args.step:
        project.process_section(project_definition.test)


if __name__ == '__main__':
    os.setpgrp()
    main()
