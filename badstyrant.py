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

class BadsTyrant(Peer):
    def post_init(self):
        print(("post_init(): %s here!" % self.id))
        self.uij = dict()
        self.dij = dict()
        self.alpha = 0.2
        self.r = 3
        self.lamb = 0.1
        self.cap = self.up_bw
        print("CAP: ", self.cap)
    
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
        # peers.sort(key=lambda p: p.id)
        # # request all available pieces from all peers!
        # # (up to self.max_requests from each)
        # for peer in peers:
        #     av_set = set(peer.available_pieces)
        #     isect = av_set.intersection(np_set)
        #     n = min(self.max_requests, len(isect))
        #     # More symmetry breaking -- ask for random pieces.
        #     # This would be the place to try fancier piece-requesting strategies
        #     # to avoid getting the same thing from multiple peers at a time.
        #     for piece_id in random.sample(isect, n):
        #         # aha! The peer has this piece! Request it.
        #         # which part of the piece do we need next?
        #         # (must get the next-needed blocks in order)
        #         start_block = self.pieces[piece_id]
        #         r = Request(self.id, peer.id, piece_id, start_block)
        #         requests.append(r)
        # return requests

        for peer in peers:
            av_set = set(peer.available_pieces)
            isect = av_set.intersection(np_set)
            n = min(self.max_requests, len(isect))
            piece_rarity = pieceRarity(peers, isect)
            # More symmetry breaking -- ask for random pieces.
            # This would be the place to try fancier piece-requesting strategies
            # to avoid getting the same thing from multiple peers at a time.
            for piece in piece_rarity[:n]:
                # aha! The peer has this piece! Request it.
                # which part of the piece do we need next?
                # (must get the next-needed blocks in order)
                start_block = self.pieces[piece[0]]
                r = Request(self.id, peer.id, piece[0], start_block)
                requests.append(r)
        return requests

    def uploads(self, requests, peers, history):
        """
        requests -- a list of the requests for this peer for this round
        peers -- available info about all the peers
        history -- history for all previous rounds

        returns: list of Upload objects.

        In each round, this will be called after requests().
        """
        chosen = []
        round = history.current_round()
        logging.debug("%s again.  It's round %d." % (
            self.id, round))
        if round == 0:
            for peer in peers:
                self.uij[peer.id] = 5
                self.dij[peer.id] = [5, 0]
        if round > 0:
            uploaders = set()
            for d in history.downloads[round-1]:
                uploaders.add(d.from_id)
                self.dij[d.from_id][0] = d.blocks #/4
                self.dij[d.from_id][1] += 1
                if self.dij[d.from_id][1] >= self.r:
                    self.uij[d.from_id] *= (1-self.lamb)

            for peer in peers:
                if peer.id not in uploaders:
                    self.uij[peer.id] *= (1+self.alpha)
                    self.dij[peer.id][1] = 0

        ordered_du = []
        for peer in peers:
            pid = peer.id
            ordered_du.append([self.dij[pid][0] / self.uij[pid], self.uij[pid], pid])
        ordered_du.sort(reverse=True)
        summation = 0
        i = 0
        while summation < self.cap and i < len(ordered_du):
            chosen.append(Upload(self.id, ordered_du[i][2], min(self.cap-summation, ordered_du[i][1])))
            summation += ordered_du[i][1]
            i += 1
        

        return chosen



        # if len(requests) == 0:
        #     logging.debug("No one wants my pieces!")
        #     chosen = []
        #     bws = []
        # else:
        #     logging.debug("Still here: uploading to a random peer")

        #     request = random.choice(requests)
        #     chosen = [request.requester_id]
        #     # Evenly "split" my upload bandwidth among the one chosen requester
        #     bws = even_split(self.up_bw, len(chosen))

        # # create actual uploads out of the list of peer ids and bandwidths
        # uploads = [Upload(self.id, peer_id, bw)
        #            for (peer_id, bw) in zip(chosen, bws)]
            
        # return uploads
