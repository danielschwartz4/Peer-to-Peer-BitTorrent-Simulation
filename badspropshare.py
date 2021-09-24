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

class BadsPropshare(Peer):
    def post_init(self):
        self.ucp = 0.1
        self.pcp = 1-self.ucp
        self.prev_uploaders = dict()
        self.random_peer = -1
        self.needNewRandom = True
    
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


        requests = []   # We'll put all the things we want here
        random.shuffle(needed_pieces)
        
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

        max_upload = 4  # max num of peers to upload to at a time
        requester_ids = list(set([r.requester_id for r in requests]))
        number_of_seeds = self.conf.agent_class_names.count("Seed")
        
        n = min(max_upload, len(requests))
        if round > 0:
            for d in history.downloads[round-1]:
                self.prev_uploaders[d.from_id] = [d.blocks, 0]
            uploaders = set(self.prev_uploaders.keys())
            isect = list(set(requester_ids).intersection(uploaders))
            total_upload = 1
            for i in isect:
                total_upload += self.prev_uploaders[i][0]
            for i in self.prev_uploaders.keys():
                self.prev_uploaders[i][1] = (self.prev_uploaders[i][0] / total_upload) * self.pcp
            print("HHH", self.prev_uploaders)

        # chosen = 0
        # for i in requester_ids:
        #     chosen.append(Upload(self.id, i, prev_uploaders[i]))
        # return chosen




        if n == 0:
            chosen = []
            bws = []
        else:
            chosen = []
            # !! Choose prioritized request instead
            topRequesters, notTopRequesters = recipocateUploads(history, requester_ids)
            for topRequest in topRequesters[:n-1]:
                notTopRequesters.remove(topRequest[0])
                chosen.append(Upload(self.id, topRequest[0], int(self.up_bw//max_upload)))

            if len(topRequesters) < n - 1:
                for i in range(n - 1 - len(topRequesters)):
                    if notTopRequesters != []:
                        randomUnchock = random.choice(notTopRequesters)
                        notTopRequesters.remove(randomUnchock)
                        chosen.append(Upload(self.id, randomUnchock, int(self.up_bw//max_upload)))
            if round % 3 == 0 or self.needNewRandom:
                if notTopRequesters != []:
                    self.random_peer = random.choice(notTopRequesters)
                    self.needNewRandom = False
                else:
                    self.needNewRandom = True
            
            chosen.append(Upload(self.id, self.random_peer, int(self.up_bw//max_upload)))

        return chosen
