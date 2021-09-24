import collections
import random
import copy

def blockRarity(peers, np_set):
	d = {}
	random.shuffle(peers)
	for peer in peers:
		av_set = set(peer.available_pieces)
		isect = list(av_set.intersection(np_set))
		random.shuffle(isect)
		for piece in isect:
			if piece in d:
				d[piece][0][0] += 1
				d[piece][1].append(peer)
			else:
				d[piece] = [[1], [peer]]

	values = []
	for key, value in d.items():
		#Value in dict of the form [[int], [Peers]]
		values.append([key, value[0][0], value[1]])
		#Value in array values of the form [piece_id, int, [Peers]]
	values.sort(key = lambda x: x[1])
	# print("ERIC: ", values)
	return values

def pieceRarity(peers, isect):
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
	#print("ERIC: ", values)
	return values


def recipocateUploads(history, copyRequester_ids ):
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
	

	# uploads = []
	# uploadDict = {}
	# for request in requests:
	# 	if request.requester_id in uploadDict:
	# 		uploadDict[request.requester_id][1].append(request)
	# 	else:
	# 		if request.requester_id in peersBW:
	# 			peerBW = peersBW[request.requester_id]
	# 		else:
	# 			peerBW = 0
	# 		#peerNumber = int(request.requester_id[7:]) + number_of_seeds - 1
	# 		uploadDict[request.requester_id] = [[peerBW], [request]]

	# for key, value in uploadDict.items():
	# 	uploads.append([key, value[0][0], value[1]])

	# sorted(uploads, key=lambda value: value[1])

	# #if len(uploads) >= slots_available:
	# #print("DAN: ", uploads)
	# topUploads = uploads[:slots_available - 1]
	# notTopUploads = uploads[slots_available - 1:]
	# return topUploads, notTopUploads

def mostGenerous(peer_ids):
	# Update their receivers' average upload rate
	# generosity_arr = []
	# for peer_id in peer_ids:
	# 	generosity_arr.append(getGenerosity(peer_id))
	pass


def getGenerosity(peer_id, history):
	uploads = history.uploads
	# prev_uploads = history.peer_history(peer_id).uploads
	for upload in uploads:
		print(upload)
	# avg_gen = sum(prev_uploads) / len(prev_uploads)
	# return avg_gen
