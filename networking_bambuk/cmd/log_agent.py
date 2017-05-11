import eventlet
import sys

from networking_bambuk.common import config
from networking_bambuk.common import update_actions
from networking_bambuk.common.config import timefunc
from networking_bambuk.rpc.bambuk_rpc import BambukAgentClient

from neutron.common import rpc as n_rpc

from oslo_log import log as logging


eventlet.monkey_patch()


LOG = logging.getLogger(__name__)


class LogAgentWorker(n_rpc.Service):
    """Processes the rpc."""

    def __init__(self):
        super(LogAgentWorker, self).__init__(config.host(), 'bambuk')
        self._bambuk_client = BambukAgentClient()

    def process_log(self, context, **kwargs):
        update_log = kwargs['log']
        LOG.info('log to process %s' % update_log)
        _action_touple = (update_log['obj_type'], update_log['action_type'])
        _cls_action = update_actions.ACTIONS_CLASS.get(_action_touple)
        if _cls_action:
            self._call_process(_cls_action, update_log)
            LOG.debug('Bambuk processed log: %s' % update_log)
        else:
            LOG.debug('Bambuk has no handler for log: %s' % update_log)

    @timefunc
    def _call_process(self, cls_action, b_log):
        _handler = cls_action(b_log, self._bambuk_client)
        _handler.process()



def main():
    config.init(sys.argv[1:])

    worker = LogAgentWorker()

    # Start everything.
    LOG.info('worker  initialized successfully, now running.')
    worker.start()

    while True:
        eventlet.sleep(600)


if __name__ == "__main__":
    main()