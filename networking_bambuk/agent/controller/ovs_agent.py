
from oslo_log import log as logging

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import ofp_handler
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3


LOG = logging.getLogger(__name__)


class BambukHandler(ofp_handler.OFPHandler):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(BambukHandler, self).__init__(*args, **kwargs)

    def mod_flow(self,
                 datapath,
                 cookie=0,
                 cookie_mask=0,
                 idle_timeout=0,
                 match=None,
                 actions=None,
                 priority=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, cookie=cookie,
                                idle_timeout=idle_timeout,
                                cookie_mask=cookie_mask, priority=priority,
                                match=match, instructions=inst,
                                flags=ofproto.OFPFF_SEND_FLOW_REM)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _switch_features_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        LOG.info('_switch_features_handler msg= %s' % msg)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        LOG.info('_packet_in_handler msg= %s' % msg)
        

    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def _flow_removed_handler(self, ev):
        msg = ev.msg
        LOG.info('_flow_removed_handler msg= %s' % msg)



def main():
    # TODO: run the controller
    pass
