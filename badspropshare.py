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

class BadsPropshare(Peer):
    def post_init(self):
        self.ucp = 0.1
        self.pcp = 1-self.ucp
        self.prev_uploaders = dict()
        self.random_peer = -1
        self.needNewRandom = True

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


        requests = []   # We'll put all the things we want here
        random.shuffle(needed_pieces)
        
        random.shuffle(peers)
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
        isect = set()
        bw_given = 0
        chosen = []
        if round > 0:
            for d in history.downloads[-1]:
                self.prev_uploaders[d.from_id] = d.blocks
            uploaders = set(self.prev_uploaders.keys())
            isect = list(set(requester_ids).intersection(uploaders))

            if isect != []:
                total_blocks = 0
                for requester_id in isect:
                    total_blocks += self.prev_uploaders[requester_id]
                for requester_id in isect:
                    new_bw = ((self.prev_uploaders[requester_id] / total_blocks) * self.pcp * self.up_bw)//1
                    bw_given += new_bw
                    requester_ids.remove(requester_id)
                    chosen.append(Upload(self.id, requester_id, new_bw))


        if len(chosen) < n - 1:
            for i in range(n - 1 - len(chosen)):
                if requester_ids != []:
                    randomUnchock = random.choice(requester_ids)
                    requester_ids.remove(randomUnchock)
                    bw_given += (self.up_bw - bw_given)/(n - len(chosen))
                    chosen.append(Upload(self.id, requester_ids, (self.up_bw - bw_given)/(n - len(chosen)) ))

        if round % 3 == 0 or self.needNewRandom:
            if requester_ids != []:
                self.random_peer = random.choice(requester_ids)
                self.needNewRandom = False
            else:
                self.needNewRandom = True
            
        chosen.append(Upload(self.id, self.random_peer, int(self.up_bw - bw_given)))

        return chosen
