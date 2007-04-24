#generate.py
#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2006-2007 Michael Curran <mick@kulgan.net>
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

"""Script to generate needed com interfaces and language files"""
import os
import sys
from glob import glob
import comtypesClient
import compileall

COM_INTERFACES = (
	("MS HTML", comtypesClient.GetModule, "mshtml.tlb"),
	("IAccessible 2", comtypesClient.GetModule, "lib/ia2.tlb"),
	("IService Provider library", comtypesClient.GetModule, "lib/servprov.tlb"),
	("MS Active Accessibility", comtypesClient.GetModule, "oleacc.dll"),
	("SAPI 5", comtypesClient.CreateObject, "Sapi.SPVoice"),
	("SAPI 4", comtypesClient.CreateObject, "ActiveVoice.ActiveVoice"),
)
COMPILE_DIRS = ("appModules", "synthDrivers")

def main():
	print "COM interfaces:"
	for desc, func, interface in COM_INTERFACES:
		print "%s:" % desc,
		try:
			func(interface)
			print "done."
		except:
			print "not found."
	print

	print "Language files:"
	poFiles=glob('locale/*/LC_MESSAGES/nvda.po')
	for f in poFiles:
		print f
		os.spawnv(os.P_WAIT,r"%s\python.exe"%sys.exec_prefix,['python',r'"%s\Tools\i18n\msgfmt.py"'%sys.exec_prefix,f])
	print

	print "Byte code compilation:"
	for dir in COMPILE_DIRS:
		compileall.compile_dir(dir, maxlevels=0)

if __name__ == "__main__":
	main()
