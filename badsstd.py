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

class BadsStd(Peer):
    def post_init(self):
        print(("post_init(): %s here!" % self.id))
        self.dummy_state = dict()
        self.dummy_state["cake"] = "lie"
        self.random_peer = -1
    
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
        
        block_rarity = blockRarity(peers, np_set)
        n = min(self.max_requests, len(block_rarity))
        for piece_info_index in range(n):
            piece_info = block_rarity[piece_info_index]
            piece_id = piece_info[0]
            start_block = self.pieces[piece_id]
            #print(piece_info[2])
            random.shuffle(piece_info[2])
            print(piece_info[2])
            for peer in piece_info[2]:
                r = Request(self.id, peer.id, piece_id, start_block)
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
        round = history.current_round()
        logging.debug("%s again.  It's round %d." % (
            self.id, round))
        # One could look at other stuff in the history too here.
        # For example, history.downloads[round-1] (if round != 0, of course)
        # has a list of Download objects for each Download to this peer in
        # the previous round.

        max_upload = 4  # max num of peers to upload to at a time
        requester_ids = list(set([r.requester_id for r in requests]))
        number_of_seeds = self.conf.agent_class_names.count("Seed")
        
        n = min(max_upload, len(requests))
        #
        # print("HERE")
        # print(n)
        # print((requests))
        if n == 0:
            logging.debug("No one wants my pieces!")
            chosen = []
            bws = []
        else:
            chosen = []
            logging.debug("Still here: uploading to a random peer")
            # change my internal state for no reason
            self.dummy_state["cake"] = "pie"
            # !! Choose prioritized request instead
            topRequesters, notTopRequesters = recipocateUploads(peers, requests, requester_ids, number_of_seeds, n, history)
            
            
            for topRequest in topRequesters:
                chosen.append(Upload(self.id, topRequest[0], int(self.up_bw//max_upload)))

            if len(topRequesters) < 3:
                for i in range(n - 1 - len(topRequesters)):
                    randomUnchock = random.choice(notTopRequesters)
                    notTopRequesters.remove(randomUnchock)
                    chosen.append(Upload(self.id, randomUnchock, int(self.up_bw//max_upload)))
            if round % 3 == 0:
                self.random_peer = random.choice(notTopRequesters)
            
            chosen.append(Upload(self.id, self.random_peer, int(self.up_bw//max_upload)))
            #print("BENJAMIN: ", chosen)
        #     else:
        #         print("BENJAMIN!!")
        #         #Choose a random request from all requests when we only have one spot
        #         request = random.choice(requests)
        #         chosen.append(request)
        #     # Evenly "split" my upload bandwidth among the one chosen requester
        #     bws = even_split(self.up_bw, len(chosen))

        # # create actual uploads out of the list of peer ids and bandwidths
        # uploads = [Upload(self.id, peer_id, bw)
        #            for (peer_id, bw) in zip(chosen, bws)]
            
        return chosen
