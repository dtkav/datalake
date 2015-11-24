# Copyright 2015 Planet Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import click
from datalake import Archive, Translator, TranslatorError, get_crtime, \
    CreationTimeError, Uploader, Enqueuer
import os
from dotenv import load_dotenv
from datalake_common.metadata import InvalidDatalakeMetadata
from datalake_common.errors import InsufficientConfiguration
import time


DEFAULT_CONFIG = '/etc/datalake.env'

archive = None


def clean_up_datalake_errors(f):
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (InvalidDatalakeMetadata,
                TranslatorError,
                CreationTimeError,
                InsufficientConfiguration) as e:
            raise click.UsageError(e.message)
    return wrapped


epilog = '''
Other influential configuration variables include:

CRTIME: Path to the crtime utility used to get the creation time of a file on
Linux. See https://github.com/planetlabs/crtime/.

DATALAKE_DEFAULT_WHERE: Some operations require a --where argument so that they
can form complete metadata for a file. If --where is not provided,
DATALAKE_DEFAULT_WHERE will be used if it is set. For example, it may make
sense in some contexts to set DATALAKE_DEFAULT_WHERE to the hostname of the
machine running the client.

DATALAKE_QUEUE_DIR: The directory where enqueue will place files for uploader
to eventually upload.
'''


@click.group(invoke_without_command=True, epilog=epilog)
@click.version_option()
@click.pass_context
@click.option('-c', '--config',
              help=('config file. The format is just single lines with '
                    'VAR=VALUE. If ' + DEFAULT_CONFIG + ' exists it will '
                    'be read. Config file values can be overridden by '
                    'environment variables, which can be overridded by '
                    'command-line arguments.'))
@click.option('-u', '--storage-url',
              help=('The URL to the top-level storage resource where '
                    'datalake will archive all the files (e.g., '
                    's3://my-datalake). DATALAKE_STORAGE_URL is the '
                    'config/environment variable'),
              envvar='DATALAKE_STORAGE_URL')
@click.option('-k', '--aws-access-key-id',
              help=('The AWS access key used to read and write s3. '
                    'AWS_ACCESS_KEY_ID is the configuration/environment '
                    'variable.'),
              envvar='AWS_ACCESS_KEY_ID')
@click.option('-s', '--aws-secret-access-key',
              help=('The AWS secret key used to read and write s3.'
                    'AWS_SECRET_ACCESS_KEY is the configuration/environment '
                    'variable.'),
              envvar='AWS_SECRET_ACCESS_KEY')
@click.option('-r', '--aws-region',
              help=('The AWS region where files should be stored. '
                    'AWS_REGION is the configuration/environment '
                    'variable.'),
              envvar='AWS_REGION')
def cli(ctx, **kwargs):
    _read_config_file(kwargs.pop('config'))
    _update_environment(**kwargs)
    _subcommand_or_fail(ctx)


def _update_environment(**kwargs):
    for k, v in kwargs.iteritems():
        if v is None:
            continue
        if not k.startswith('aws'):
            k = 'DATALAKE_' + k
        k = k.upper()
        os.environ[k] = v


def _read_config_file(config):
    if config is None:
        if os.path.exists(DEFAULT_CONFIG):
            load_dotenv(DEFAULT_CONFIG)
    elif os.path.exists(config):
        load_dotenv(config)
    else:
        raise click.UsageError('Config file {} not exist'.format(config))


def _subcommand_or_fail(ctx):
    if ctx.invoked_subcommand is None:
        ctx.fail('Please specify a command.')


def _prepare_archive_or_fail():
    global archive
    archive = Archive()


# So, I fully appreciate the dissonance of "required options." But we have lots
# of required arguments, and I want to allow them in any order and I want their
# self-documenting feature.
@cli.command()
@click.option('--start')
@click.option('--end')
@click.option('--where')
@click.option('--what')
@click.option('--work-id')
@click.argument('file')
def push(**kwargs):
    _prepare_archive_or_fail()
    _push(**kwargs)


@clean_up_datalake_errors
def _push(**kwargs):
    filename = kwargs.pop('file')
    kwargs = _evaluate_arguments(filename, **kwargs)
    url = archive.prepare_metadata_and_push(filename, **kwargs)
    click.echo('Pushed {} to {}'.format(filename, url))


def _evaluate_arguments(filename, **kwargs):
    for t in ['start', 'end']:
        if t in kwargs:
            kwargs[t] = _evaluate_time(filename, kwargs[t])
    return kwargs


def _evaluate_time(filename, t):
    if t == 'crtime':
        return int(get_crtime(filename) * 1000)
    if t == 'now':
        return int(time.time() * 1000)
    return t


@cli.command()
@click.argument('translation-expression')
@click.argument('file')
def translate(**kwargs):
    _translate(**kwargs)


@clean_up_datalake_errors
def _translate(**kwargs):
    t = Translator(kwargs['translation_expression'])
    click.echo(t.translate(kwargs['file']))


@cli.command()
@click.option('--start')
@click.option('--end')
@click.option('--where')
@click.option('--what')
@click.option('--work-id')
@click.argument('file')
def enqueue(file, **kwargs):
    _enqueue(file, **kwargs)


@clean_up_datalake_errors
def _enqueue(file, **kwargs):
    kwargs = _evaluate_arguments(file, **kwargs)
    e = Enqueuer()
    e.enqueue(file, **kwargs)
    click.echo('Enqueued {}'.format(file))


@cli.command()
@click.option('--timeout', type=float)
def uploader(**kwargs):
    _uploader(**kwargs)


@clean_up_datalake_errors
def _uploader(**kwargs):
    from datalake.logging_helpers import prepare_logging
    prepare_logging()
    _prepare_archive_or_fail()
    u = Uploader(archive, os.environ.get('DATALAKE_QUEUE_DIR'))
    u.listen(**kwargs)
