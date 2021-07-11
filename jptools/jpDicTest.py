# coding: UTF-8
# A part of NonVisual Desktop Access (NVDA)
# by Takuya Nishimoto (NVDA Japanese Team)
# jpDicTest.py for testing source/nvdajp_dic.py
# Usage:
# > miscDeps\tools\msgfmt.exe source\locale\ja\LC_MESSAGES\nvda.po -o source\locale\ja\LC_MESSAGES\nvda.mo
# > cd jptools
# > python jpDicTest.py

from __future__ import unicode_literals, print_function
import unittest
import sys, os

sys.path.append(os.path.normpath(os.path.join(os.getcwd(), "mocks")))
sys.path.append(r"..\source")
sys.path.append(r"..\miscdeps\python")
import languageHandler

languageHandler.setLanguage("ja")
import jpUtils

# import locale
import gettext

gettext.translation("nvda", localedir=r"..\source\locale", languages=["ja"]).install(
    True
)

items = [
    ("a", "半角 英字 エー アルファー", "半角 a"),
    ("A", "半角 英字 オオモジ  エー アルファー", "半角 A"),
    ("あ", "ヒラガナ あ", "ヒラガナ あ"),
    ("ア", "カタカナ ア", "カタカナ ア"),
    ("あア", "ヒラガナ あ カタカナ ア", "ヒラガナ あ カタカナ ア"),
    ("を", "ヒラガナ オワリノ オ", "ヒラガナ を"),
    ("ヲ", "カタカナ オワリノ オ", "カタカナ ヲ"),
    ("123", "半角 イチ ニ サン", "半角 123"),
    ("１２３", "全角 イチ ニ サン", "全角 １２３"),
    ("1.23", "半角 イチ .ニ サン", "半角 1.23"),
    ("１．２３", "全角 イチ ピリオド ニ サン", "全角 １．２３"),
    # ('1(23)', '半角 イチ カッコ ニ サン カッコトジ', '半角 1(23)'),
    # ('１（２３）', '全角 イチ カッコ ニ サン カッコトジ', '全角 １（２３）'),
    ("川", "サンボンガワノ カワ", "サンボンガワノ カワ"),
    ("^", "半角 ベキジョー", "半角 ベキジョー"),
]


class JpDicTestCase(unittest.TestCase):
    def test_getDiscriminantReading(self):
        for i in items:
            a, b, c = i[0], i[1], i[2]
            s = jpUtils.getDiscriminantReading(a, sayCapForCapitals=True)
            # print("name(%s) correctS(%s) actualS(%s)" % (a, b, s))
            self.assertEqual(b, s)
            t = jpUtils.getDiscrptionForBraille(a)
            # print("name(%s) correctB(%s) actualB(%s)" % (a, c, t))
            self.assertEqual(c, t)


if __name__ == "__main__":
    unittest.main()
