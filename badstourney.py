#!/usr/bin/python

# This is a dummy peer that just illustrates the available information your peers 
# have available.

# You'll want to copy this file to AgentNameXXX.py for various versions of XXX,
# probably get rid of the silly logging messages, and then add more logic.

import random
import logging

from messages import Upload, Request
from util import even_split
from peer import Peer
from badsutil import *

class BadsTourney(Peer):
    def post_init(self):
        print(("post_init(): %s here!" % self.id))
        self.dummy_state = dict()
        self.dummy_state["cake"] = "lie"
        self.dij = dict()
    
    def requests(self, peers, history):
        """
        peers: available info about the peers (who has what pieces)
        history: what's happened so far as far as this peer can see

        returns: a list of Request() objects

        This will be called after update_pieces() with the most recent state.
        """
        needed = lambda i: self.pieces[i] < self.conf.blocks_per_piece
        needed_pieces = list(filter(needed, list(range(len(self.pieces)))))
        np_set = set(needed_pieces)  # sets support fast intersection ops.


        logging.debug("%s here: still need pieces %s" % (
            self.id, needed_pieces))

        logging.debug("%s still here. Here are some peers:" % self.id)
        for p in peers:
            logging.debug("id: %s, available pieces: %s" % (p.id, p.available_pieces))

        logging.debug("And look, I have my entire history available too:")
        logging.debug("look at the AgentHistory class in history.py for details")
        logging.debug(str(history))

        requests = []   # We'll put all the things we want here
        # Symmetry breaking is good...
        random.shuffle(needed_pieces)
        
        # Sort peers by id.  This is probably not a useful sort, but other 
        # sorts might be useful
        random.shuffle(peers)
        for peer in peers:
            av_set = set(peer.available_pieces)
            isect = list(av_set.intersection(np_set))
            random.shuffle(isect)
            n = min(self.max_requests, len(isect))
            piece_rarity = pieceRarity(peers, isect)
            for piece in piece_rarity[:n]:
                start_block = self.pieces[piece[0]]
                r = Request(self.id, peer.id, piece[0], start_block)
                requests.append(r)
        #random.shuffle(requests)
        return requests

    def uploads(self, requests, peers, history):
        """
        requests -- a list of the requests for this peer for this round
        peers -- available info about all the peers
        history -- history for all previous rounds

        returns: list of Upload objects.

        In each round, this will be called after requests().
        """
        delta = .2
        max_upload = 3  # max num of peers to upload to at a time
        requester_ids = list(set([r.requester_id for r in requests]))
        
        n = min(max_upload, len(requests))

        chosen = []
        round = history.current_round()
        logging.debug("%s again.  It's round %d." % (
            self.id, round))
        if round == 0:
            for peer in peers:
                self.dij[peer.id] = float(self.up_bw/4)
        if round > 0:
            uploaders = set()
            for d in history.downloads[-1]:
                uploaders.add(d.from_id)
                oldDIJ = self.dij[d.from_id]
                self.dij[d.from_id] = float(d.blocks) + float(oldDIJ)*delta

            for peer in peers:
                if peer.id not in uploaders and peer.id in requester_ids:
                    self.dij[peer.id] = self.dij[peer.id]*delta

        ordered_du = []
        for peer in peers:
            pid = peer.id
            if "Seed" not in pid:
                ordered_du.append([self.dij[pid], pid])
        ordered_du.sort(reverse=True)
        i = 0
        upload_count = 0
        while upload_count < max_upload and len(requester_ids) > i:
            if ordered_du[i][1] in requester_ids:
                chosen.append(Upload(self.id, ordered_du[i][1], self.up_bw/n))
                upload_count += 1
            i += 1


        return chosen
