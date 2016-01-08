from charms.reactive import when, when_not, set_state
from charms.hadoop import get_hadoop_base
from charmhelpers.core import hookenv
from charmhelpers.core.hookenv import role_and_interface_to_relations as rel_names
from jujubigdata.handlers import HDFS, YARN
from jujubigdata import utils


HDFS_RELATION = rel_names('requires', 'hdfs') or rel_names('provides', 'datanode')
YARN_RELATION = rel_names('requires', 'yarn') or rel_names('provides', 'nodemanager')


@when_not('hadoop.installed')
def fetch_resources():
    hadoop = get_hadoop_base()
    if hadoop.verify_resources():
        set_state('resources.available')


@when('resources.available')
@when_not('hadoop.installed')
def install_hadoop():
    hadoop = get_hadoop_base()
    hadoop.install()
    set_state('hadoop.installed')


if HDFS_RELATION:
    @when('hadoop.installed', '{hdfs}.related'.format(hdfs=HDFS_RELATION[0]))
    def set_hdfs_spec(namenode):
        hadoop = get_hadoop_base()
        namenode.set_local_spec(hadoop.spec())

    @when('{hdfs}.spec.mismatch'.format(hdfs=HDFS_RELATION[0]))
    def hdfs_spec_mismatch(namenode):
        hookenv.status_set('blocked',
                           'Spec mismatch with NameNode: {} != {}'.format(
                               namenode.local_spec(), namenode.remote_spec()))

    @when('{hdfs}.ready'.format(hdfs=HDFS_RELATION[0]))
    def configure_hdfs(namenode):
        hadoop = get_hadoop_base()
        hdfs = HDFS(hadoop)
        utils.update_kv_hosts(namenode.hosts_map())
        utils.manage_etc_hosts()
        hdfs.configure_hdfs_base(namenode.namenodes()[0], namenode.port())
        set_state('hadoop.hdfs.configured')


if YARN_RELATION:
    @when('hadoop.installed', '{yarn}.related'.format(yarn=YARN_RELATION[0]))
    def set_yarn_spec(resourcemanager):
        hadoop = get_hadoop_base()
        resourcemanager.set_local_spec(hadoop.spec())

    @when('{yarn}.spec.mismatch'.format(yarn=YARN_RELATION[0]))
    def yarn_spec_mismatch(resourcemanager):
        hookenv.status_set('blocked',
                           'Spec mismatch with ResourceManager: {} != {}'.format(
                               resourcemanager.local_spec(), resourcemanager.remote_spec()))

    @when('{yarn}.ready'.format(yarn=YARN_RELATION[0]))
    def configure_yarn(resourcemanager):
        hadoop = get_hadoop_base()
        yarn = YARN(hadoop)
        utils.update_kv_hosts(resourcemanager.hosts_map())
        utils.manage_etc_hosts()
        yarn.configure_yarn_base(resourcemanager.resourcemanagers()[0], resourcemanager.port(),
                                 resourcemanager.hs_http(), resourcemanager.hs_ipc())
        set_state('hadoop.yarn.configured')