# coding: utf-8
# source/local/ja/characters.dic を Unicode 番号順に並べる

from __future__ import print_function, unicode_literals

import csv
import unicodedata

from _checkCharDesc import read_characters_file

#items = read_characters_file(r'..\source\locale\ja\characters.dic')
with open(r'..\source\locale\ja\characters.dic') as file:
	items = {}
	for src in file:
		src = src.rstrip().decode('utf-8')
		if not src:
			continue
		elif src[0] == '#':
			continue
		elif src[0:2] == '\\#': 
			line = '#' + src[2:]
		else:
			line = src
		a = line.split('\t')
		if len(a) >= 4:
			items[int(a[1], 16)] = src

for k in sorted(items.keys()):
	print(items[k].encode('utf-8', 'ignore'))

