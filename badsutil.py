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
		print(key, value)
		values.append([key, value[0][0], value[1]])
	sorted(values, key=lambda value: value[1])
	return values

