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

class BadsStd(Peer):
    def post_init(self):
        print(("post_init(): %s here!" % self.id))
        self.dummy_state = dict()
        self.dummy_state["cake"] = "lie"
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
        round = history.current_round()
        logging.debug("%s again.  It's round %d." % (
            self.id, round))
        # One could look at other stuff in the history too here.
        # For example, history.downloads[round-1] (if round != 0, of course)
        # has a list of Download objects for each Download to this peer in
        # the previous round.

        max_upload = 4  # max num of peers to upload to at a time
        requester_ids = list(set([r.requester_id for r in requests]))
        
        n = min(max_upload, len(requests))

        if n == 0:
            chosen = []
            bws = []
        else:
            chosen = []
            # !! Choose prioritized request instead
            topRequesters, notTopRequesters = self.recipocateUploads(history, requester_ids)
            for topRequest in topRequesters[:n-1]:
                notTopRequesters.remove(topRequest[0])
                chosen.append(Upload(self.id, topRequest[0], int(self.up_bw//n)))

            if len(topRequesters) < n - 1:
                for i in range(n - 1 - len(topRequesters)):
                    if notTopRequesters != []:
                        randomUnchock = random.choice(notTopRequesters)
                        notTopRequesters.remove(randomUnchock)
                        chosen.append(Upload(self.id, randomUnchock, int(self.up_bw//n)))
            if round % 3 == 0 or self.needNewRandom:
                if notTopRequesters != []:
                    self.random_peer = random.choice(notTopRequesters)
                    self.needNewRandom = False
                else:
                    self.needNewRandom = True
            
            chosen.append(Upload(self.id, self.random_peer, int(self.up_bw//n)))

        return chosen
