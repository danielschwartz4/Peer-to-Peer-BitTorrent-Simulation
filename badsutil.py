import collections

def blockRarity(peers, np_set):
	d = {}
	
	for peer in peers:
		av_set = set(peer.available_pieces)
		isect = av_set.intersection(np_set)
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
	sorted(values, key=lambda value: value[1])
	return values

def recipocateUploads(peers, requests, requester_ids, number_of_seeds):
	uploads = []
	uploadDict = {}
	for request in requests:
		if request.requester_id in uploadDict:
			uploadDict[requester_id][1].append(request)
		else:
			peerNumber = int(request.requester_id[7:]) + number_of_seeds - 1
			peerBw = peers[peerNumber].up_bw
			uploadDict[requester_id] = [[peerBw], [request]]

	for key, value in uploadDict.items():
		uploads.append([key, value[0][0], value[1]])

	sorted(uploads, key=lambda value: value[1])
	return "TODO"
