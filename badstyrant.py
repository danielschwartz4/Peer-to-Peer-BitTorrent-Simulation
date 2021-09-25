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

class BadsTyrant(Peer):
    def post_init(self):
        print(("post_init(): %s here!" % self.id))
        self.uij = dict()
        self.dij = dict()
        self.alpha = 0.2
        self.r = 3
        self.lamb = 0.1
        self.cap = self.up_bw
        self.history_requesters = []

    def pieceRarity(self, peers, isect):
        # Using Dictionary comprehension
        d = {}
        for peer in peers:
            for piece in isect:
                if piece in peer.available_pieces:
                    if piece in d:
                        d[piece] += 1
                    else:
                        d[piece] = 1

        values = []
        for key, value in d.items():
            #Value in dict of the form [[int], [Peers]]
            values.append([key, value])
            #Value in array values of the form [piece_id, int, [Peers]]
        values.sort(key = lambda x: x[1])
        return values


    def recipocateUploads(self, history, copyRequester_ids ):
        peersBW = {}
        for i in range(1,3):
            for download in history.downloads[-i]:
                if download.from_id in copyRequester_ids:
                    if download.from_id in peersBW:
                        peersBW[download.from_id] += download.blocks
                    else:
                        peersBW[download.from_id] = download.blocks 

        sortPeersBW = []
        for key, value in peersBW.items():
            sortPeersBW.append([key, value])
        sortPeersBW.sort(key = lambda x: x[1], reverse=True)
        return sortPeersBW, copyRequester_ids
    
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
        
       
        random.shuffle(peers)
        requesters_temp = set()
        for peer in peers:
            av_set = set(peer.available_pieces)
            isect = list(av_set.intersection(np_set))
            random.shuffle(isect)
            n = min(self.max_requests, len(isect))
            piece_rarity = self.pieceRarity(peers, isect)
            for piece in piece_rarity[:n]:
                start_block = self.pieces[piece[0]]
                r = Request(self.id, peer.id, piece[0], start_block)
                requests.append(r)
                requesters_temp.add(peer.id)
        random.shuffle(requests)
        self.history_requesters = list(requesters_temp)
        return requests

    def uploads(self, requests, peers, history):
        """
        requests -- a list of the requests for this peer for this round
        peers -- available info about all the peers
        history -- history for all previous rounds

        returns: list of Upload objects.

        In each round, this will be called after requests().
        """
        requester_ids = list(set([r.requester_id for r in requests]))
        chosen = []
        round = history.current_round()
        logging.debug("%s again.  It's round %d." % (
            self.id, round))
        if round == 0:
            for peer in peers:
                self.uij[peer.id] = self.up_bw/4
                self.dij[peer.id] = [self.up_bw/4, 0]
        if round > 0:
            uploaders = set()
            for d in history.downloads[-1]:
                uploaders.add(d.from_id)
                self.dij[d.from_id][0] = d.blocks
                self.dij[d.from_id][1] += 1
                if self.dij[d.from_id][1] >= self.r:
                    self.uij[d.from_id] *= (1-self.lamb)


            for peer in peers:
                if peer.id not in uploaders and peer.id in self.history_requesters:
                    self.uij[peer.id] *= (1+self.alpha)
                    self.dij[peer.id][1] = 0

        ordered_du = []
        for peer in peers:
            pid = peer.id
            if "Seed" not in pid:
                ordered_du.append([self.dij[pid][0] / self.uij[pid], self.uij[pid], pid, self.dij[pid][0]])
        ordered_du.sort(reverse=True)
        summation = 0
        i = 0

        while summation < self.cap and i < len(ordered_du):
            if ordered_du[i][2] in requester_ids:
                chosen.append(Upload(self.id, ordered_du[i][2], min(self.cap-summation, ordered_du[i][1])))
                summation += min(self.cap-summation, ordered_du[i][1])
            i += 1

        return chosen
