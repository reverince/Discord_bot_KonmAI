import discord
from discord.ext import commands
from discord.ext.commands import Bot
from lxml import html
import datetime
import json
import requests
import random
import re
import time

PREFIX = '`'
DESCRIPTION = ''
GAME = '도움말은 `도움'
THEME_COLOR = 0x00a0ee
URL = 'https://discord.gg/E6eXnpJ'
ICON_URL = 'https://ko.gravatar.com/userimage/54425936/ab5195334dd95d4171ac9ddab1521a5b.jpeg'

CUSTOM_CHO_QUIZ_FILE = 'custom_cho_quiz.dat'
MEMORY_FILE = 'memory.dat'

cho_quizs = {} # 초성퀴즈 관리
bj_games = {} # 블랙잭 관리
lots_games = {} # 제비뽑기 관리
fortune_users = {} # 운세 관리

def korea_time_string():
	"""(REPL.IT 전용) UTC를 한국 시간으로 변환"""
	tm = time.gmtime()
	tm_str = '{}년 {}월 {}일 {}:{}:{}'.format(tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour+9, tm.tm_min, tm.tm_sec)

	return tm_str

def bignumrize(numstr):
	"""Discord 이모지로 숫자 강조"""
	ret = re.sub('0', ':zero:', re.sub('1', ':one:', re.sub('2', ':two:', re.sub('3', ':three:', re.sub('4', ':four:', re.sub('5', ':five:', re.sub('6', ':six:', re.sub('7', ':seven:', re.sub('8', ':eight:', re.sub('9', ':nine:', numstr))))))))))

	return ret

def daum_search(keyword):
	page = requests.get('http://dic.daum.net/search.do?q=' + keyword)
	tree = html.fromstring(page.content)

	ret = ''
	i = 1
	while True:
		ret += '\n'
		word = tree.xpath('//div[@id="mArticle"]/div[1]/div[2]/div[2]/div['+str(i)+']/div[1]/strong[1]//text()')
		if len(word) == 0: break
		ret += ' '.join(''.join(word).split()) + '\n'

		meanings = []
		j = 1
		while True:
			meaning = tree.xpath('//div[@id="mArticle"]/div[1]/div[2]/div[2]/div['+str(i)+']/ul/li['+str(j)+']//text()')
			if len(meaning) == 0: break
			meaning.insert(1, ' ')
			meanings.append(''.join(meaning))
			meanings.append(' ')
			j += 1
		ret += ''.join(meanings[:-1]) + '\n'
		i += 1
	
	return ret

def daum_realtime():
	""" 1~10위 배열 반환 """
	response = requests.get('https://www.daum.net/')
	tree = html.fromstring(response.content)

	word = tree.xpath('//span[@class="txt_issue"]//text()')
	word = list(filter(lambda x: x != '\n', word))

	ret = []
	for i in range(0, 20, 2):
		ret.append(word[i])
	
	return ret

def daum_lotto(inning=''):
	"""return [회차, 연, 월, 일, 번호...]"""
	response = requests.get('https://search.daum.net/search?w=tot&q='+inning+'%20로또%20당첨%20번호')
	tree = html.fromstring(response.content)

	ret = tree.xpath('//div[@class="lottonum"]//text()')
	ret = list(filter(lambda x: x not in [' ', '보너스'], ret))
	day = tree.xpath('//span[@class="f_date"]//text()')
	if len(day) > 0:
		day = day[0][1:-3].split('.') # (0000.00.00추첨) -> 0000.00.00
		for i in range(0, 3):
			ret.insert(0, day[2-i])
	inning = tree.xpath('//span[@class="f_red"]//text()')
	if len(inning) > 0:
		ret.insert(0, inning[0])

	return ret

BASE, CHO, JUNG = 44032, 588, 28
CHO_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
CHO_LITE_LIST = ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅅ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
PARSED_CHO_LIST = ['%A1', '%A2', '%A4', '%A7', '%A8', '%A9', '%B1', '%B2', '%B3', '%B5', '%B6', '%B7', '%B8', '%B9', '%BA', '%BB', '%BC', '%BD', '%BE']

def cho(keyword):
	""" 단어를 초성으로 """
	split_keyword_list = list(keyword)
	result = []
	for letter in split_keyword_list:
		if re.match('.*[가-힣]+.*', letter) is not None:
			char_code = ord(letter) - BASE
			cho_code = int(char_code / CHO)
			result.append(CHO_LIST[cho_code])
		else:
			result.append(letter)

	return ''.join(result)

def cho_gen_lite(length):
	result = ''
	for _ in range(0, length):
		result += CHO_LITE_LIST[random.randint(0, 13)]

	return result

def jaum_search(genre=None, chos=cho_gen_lite(random.randint(2,3))):
	""" genre : movie, music, animal, dic, game, people, book """
	query = ''
	for i in range(0, len(chos)):
		query += '%A4' + PARSED_CHO_LIST[CHO_LIST.index(chos[i])]
	if genre == None:
			page = requests.get('http://www.jaum.kr/index.php?w='+query)
	else:
		page = requests.get('http://www.jaum.kr/index.php?w='+query+'&k='+genre)
	tree = html.fromstring(page.content)
	
	result = tree.xpath('//*[@id="container"]/div/table/tbody/tr[1]/td[1]//text()')

	return result

def jaum_quiz(genre=None):
	if genre == "영화": genre = 'movie'
	elif genre == "음악": genre = 'music'
	elif genre == "동식물": genre = 'animal'
	elif genre == "사전": genre = 'dic'
	elif genre == "게임": genre = 'game'
	elif genre == "인물": genre = 'people'
	elif genre == "책": genre = 'book'
	else:	return None

	answers = []
	while len(answers) == 0:
		answers = jaum_search(genre, cho_gen_lite(random.randint(2,3)))
	answer = re.sub(r'\s+$', '', re.sub(r'^\s+', '', re.sub(r'(?i)[A-Z().]', '', random.choice(answers))))

	print('정답 : '+answer) #DEBUG
	return answer

def josa(word, j):
	if j in ['은', '는', '이', '가', '을', '를', '으로', '로']:
		last_char = word[-1]
		has_jong = True if (ord(last_char) - BASE) % 28 > 0 else False
		if j in ['은', '는']:
			return '은' if has_jong else '는'
		elif j in ['이', '가']:
			return '이' if has_jong else '가'
		elif j in ['을', '를']:
			return '을' if has_jong else '를'
		elif j in ['으로', '로']:
			return '으로' if has_jong else '로'
		else:
			raise Exception('josa 함수에 잘못된 인수 전달.')

class ChoQuiz:
	def __init__(self):
		self.genre = None
		self.count = None
		self.answer = None
		self.score = None
	
	@classmethod
	def find(cls, channel):
		global cho_quizs

		return cho_quizs[channel] if channel in cho_quizs.keys() else None
	
	@classmethod
	def start(cls, channel, genre, count, answer):
		global cho_quizs

		cho_quizs[channel] = ChoQuiz()
		cho_quizs[channel].genre = genre
		cho_quizs[channel].count = count
		cho_quizs[channel].answer = answer

		return cho_quizs[channel]
	
	@classmethod
	def end(cls, channel):
		global cho_quizs
		if cho_quizs[channel] is not None:
			del cho_quizs[channel]
			ret = '초성퀴즈를 종료했어요.'
		else:
			ret = '진행 중인 초성퀴즈가 없어요.'

		return ret
	
	@classmethod
	def add_custom(cls, author, args):
		"""args: ['정답', '설', '명', ...], quizs: {'정답': ['id', 'name', '설명']}"""
		print(author)
		print(args)
		if len(args) > 1:
			try:
				with open(CUSTOM_CHO_QUIZ_FILE, 'r') as f:
					quizs = json.loads(f.read())
					f.close()
			except: # 파일이나 파일 내용이 없는 경우
				quizs = {}
			
			if args[0] in quizs: # 이미 등록된 정답
				mem = quizs[args[0]]
				if author.id == mem[0]: # 수정
					quizs[args[0]][2] = ' '.join(args[1:])
					ret = '설명을 수정했어요.'
				else:
					return '다른 유저님이 이미 등록한 정답이에요. :confused:'
			else:
				quizs[args[0]] = [author.id, author.name, ' '.join(args[1:])]
				ret = '새로운 초성퀴즈를 등록했어요.'
			
			with open(CUSTOM_CHO_QUIZ_FILE, 'w') as f:
				f.write(json.dumps(quizs))
				f.close()
			return ret
		else:
			return '` `초성 등록 정답 설명 `처럼 입력해 주세요.'

	def correct(self, channel):
		self.count -= 1
		if self.count > 0:
			self.answer = jaum_quiz(self.genre)
			return cho(self.answer)
		else:
			return ChoQuiz.end(channel)

# server: krjp, jp, as, na, eu, oc, sa, sea, ru
def pubg_profile(name, server='krjp'):
	if server is None:
		response = requests.get('https://dak.gg/profile/'+name)
	else:
		year = str(time.gmtime().tm_year)
		month = str(time.gmtime().tm_mon)
		if len(month) < 2: month = '0' + month
		response = requests.get('https://dak.gg/profile/'+name+'/'+year+'-'+month+'/'+server)
	
	tree = html.fromstring(response.content)
	data = tree.xpath('//section[@class="solo modeItem"]//text()')
	data = list(map(lambda x: re.sub('\n', '', re.sub(' ', '', x)), data))
	data = list(filter(lambda x: x != '', data))

	if len(data) >= 44:
		ret = {}
		ret['avatar'] = tree.xpath('//div[@class="userInfo"]/img/@src')[0]
		ret['solo-playtime'] = data[1]
		ret['solo-record'] = data[2]
		ret['solo-grade'] = data[3]
		ret['solo-score'] = data[4]
		ret['solo-rank'] = data[6]
		if len(data) == 45:
			ret['solo-top'] = data[7]
		i = 7 if len(data) == 44 else 8
		ret['solo-win-rating'] = data[i]	
		ret['solo-win-top'] = data[i+2]
		ret['solo-kill-rating'] = data[i+3]
		ret['solo-kill-top'] = data[i+5]
		ret['solo-kd'] = data[i+8]
		ret['solo-kd-top'] = data[i+9]
		ret['solo-winratio'] = data[i+11]
		ret['solo-winratio-top'] = data[i+12]
		ret['solo-top10'] = data[i+14]
		ret['solo-top10-top'] = data[i+15]
		ret['solo-avgdmg'] = data[i+17]
		ret['solo-avgdmg-top'] = data[i+18]
		ret['solo-games'] = data[i+20]
		ret['solo-games-top'] = data[i+21]
		ret['solo-mostkills'] = data[i+23]
		ret['solo-mostkills-top'] = data[i+24]
		ret['solo-headshots'] = data[i+26]
		ret['solo-headshots-top'] = data[i+27]
		ret['solo-longest'] = data[i+29]
		ret['solo-longest-top'] = data[i+30]
		ret['solo-survived'] = data[i+32]
		ret['solo-survived-top'] = data[i+33]
	else:
		ret = None

	return ret

def gf_times(pd_time):
	GF_TIMES = { '00:20': ['M1911', '나강 리볼버', 'P38'], '00:22': ['PPK'], '00:25': ['FNP-9', 'MP-446'], '00:28': ['USP Compact', 'Bren Ten'], '00:30': ['P08', 'C96'], '00:35': ['92식', 'P99'], '00:40': ['아스트라 리볼버', 'M9', '마카로프'], '00:45': ['토카레프'], '00:50': ['콜트 리볼버', 'Mk23'], '00:52': ['스핏파이어'], '00:53': ['K5'], '00:55': ['P7', '스테츠킨'], '01:00': ['웰로드 MKII'], '01:02': ['컨텐더'], '01:05': ['M950A', 'NZ75'], '01:10': ['그리즐리 Mk V', 'IDW', 'PP-2000'], '01:20': ['Spectre M4', 'M45'], '01:25': ['64식'], '01:30': ['MP40', '베레타 38형', 'M3'], '01:40': ['스텐 Mk.II', '마이크로 우지'], '01:50': ['F1', 'PPSh-41'], '02:00': ['MAC-10', '스콜피온'], '02:05': ['Z-62'], '02:10': ['PPS-43'], '02:15': ['UMP-9', 'UMP-45'], '02:18': ['시프카', 'PP-19-01'], '02:20': ['MP5', 'PP-90'], '02:25': ['수오미'], '02:28': ['C-MS'], '02:30': ['톰슨', 'G36C'], '02:33': ['SR-3MP'], '02:35': ['벡터', '79식'], '02:40': ['갈릴', 'SIG-510'], '02:45': ['F2000', '63식'], '02:50': ['L85A1', 'G3'], '03:00': ['StG44'], '03:10': ['OTs-12', 'G43', 'FN-49'], '03:15': ['ARX-160'], '03:20': ['AK-47', 'FNC', 'BM59'], '03:25': ['56-1식', 'XM8'], '03:30': ['AS Val', 'FAMAS', 'TAR-21', '시모노프', 'SVT-38'], '03:35': ['9A-91'], '03:40': ['G36', '리베롤:heart:', 'M14', 'SV-98'], '03:45': ['FAL'], '03:48': ['T91'], '03:50': ['95식', '97식', '한양조88식', 'OTs-44(중형제조)'], '03:52': ['K2'], '03:53': ['MDR'], '03:55': ['HK416'], '03:58': ['RFB'], '04:00': ['M1 개런드'], '04:04': ['G11'], '04:05': ['G41', 'Zas M21'], '04:09': ['AN-94'], '04:10': ['모신나강', 'T-5000'], '04:12': ['AK-12'], '04:15': ['SVD'], '04:20': ['PSG-1(중형제조)', 'G28(중형제조)'], '04:25': ['스프링필드'], '04:30': ['PTRD', 'PzB39(중형제조)'], '04:38': ['카르카노 M1891'], '04:40': ['Kar98k'], '04:42': ['카르카노 M91/38'], '04:45': ['NTW-20'], '04:50': ['WA2000', 'AAT-52', 'FG42'], '04:52': ['IWS 2000'], '04:55': ['M99'], '05:00': ['리엔필드', 'MG34', 'DP28'], '05:10': ['LWMMG'], '05:20': ['브렌'], '05:40': ['M1919A4'], '05:50': ['MG42'], '06:10': ['M2HB', 'M60'], '06:15': ['80식'], '06:20': ['Mk48', 'AEK-999'], '06:25': ['M1918', '아멜리'], '06:30': ['PK', 'MG3'], '06:35': ['네게브'], '06:40': ['MG4'], '06:45': ['MG5'], '06:50': ['PKP'], '07:15': ['NS2000'], '07:20': ['M500'], '07:25': ['KS-23'], '07:30': ['RMB-93', 'M1897'], '07:40': ['M590', 'SPAS-12'], '07:45': ['M37'], '07:50': ['Super-Shorty'], '07:55': ['USAS-12'], '08:00': ['KSG'], '08:05': ['Saiga-12'], '08:10': ['S.A.T.8'] }

	if len(pd_time) == 3: # 340
		pd_time = '0' + pd_time[0] + ':' + pd_time[1:2]
	if len(pd_time) == 4: # 0340
		pd_time = pd_time[0:2] + ':' + pd_time[2:4]
	
	return '제조시간이 **'+pd_time+'**인 전술인형: '+', '.join(GF_TIMES[pd_time])

class PlayingCard:
	
	def __init__(self, number, suit, value, point):
		self.number = number
		self.suit = suit
		self.value = value
		self.point = point

	def __str__(self):
		return self.suit + self.number

	@classmethod
	def str(cls, cards):
		return [str(card) for card in cards]

	@classmethod
	def bj_sum(cls, cards):
		ret = sum(card.value for card in cards)
		cnt_a = list(map(lambda x: x.number, cards)).count('A')
		ret += cnt_a * 10
		if ret > 21:
			for _ in range(0, cnt_a):
				ret -= 10
				if ret <= 21: break

		return ret

class Deck:
	NUMBERS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
	SUITS = [':clubs:', ':diamonds:', ':hearts:', ':spades:']
	
	def __init__(self):
		self.cards = []
		point = 1
		for i, number in enumerate(Deck.NUMBERS):
			for suit in Deck.SUITS:
				self.cards.append(PlayingCard(number, suit, min(i + 1, 10), point))
				point += 1

	def shuffle(self):
		random.shuffle(self.cards)

	def size(self):
		return len(self.cards)

	def draw(self):
		return self.cards.pop()

	def top(self):
		return self.cards[-1]  #if len(self.cards) > 0 else None

class Blackjack:
	BLACKJACK_MESSAGES = ['블랙잭!!']
	HIT_MESSAGES = ['히트.', '히트!', '히트다 히트!', '한 장 더 뽑을게요.']
	HIT_MESSAGES_FIRST = ['저는 히트할게요.']
	HIT_MESSAGES_MORE = []
	STAND_MESSAGES = ['스탠드.', '스탠드!']
	STAND_MESSAGES_HIT = ['여기까지 할게요.']
	STAND_MESSAGES_NOHIT = ['저는 바로 스탠드할게요.']
	BUST_MESSAGES_PLAYER = ['버스트!', '버스트! 욕심이었어요.']
	BUST_MESSAGES_DEALER = ['왝.', '아니!', '버스트. 저의 패배예요.']
	WIN_MESSAGES_PLAYER = ['제가 졌어요.', '저의 패배예요.', '졌어요. 제법이시군요.']
	WIN_MESSAGES_DEALER = ['제가 이겼어요!', '저의 승리예요!', '특이점은 온다!']
	DRAW_MESSAGES = ['비겼네요.', '무승부예요.', '무승부! 한 판 더 하실래요?']

	def __init__(self, player):
		self.player = player
		self.cnt_dhit = 0
		self.deck = Deck()
		self.deck.shuffle()
		self.pcards = [self.deck.draw(), self.deck.draw()]  # player
		self.dcards = [self.deck.draw(), self.deck.draw()]  # dealer
		self.calc_psum()
		self.calc_dsum()

	def __str__(self):
		return 'KonmAI의 패: {} ({} + ?)\n{}님의 패: {} ({})'.format(
		    ', '.join(PlayingCard.str(self.dcards[0:-1])),
		    str(PlayingCard.bj_sum(self.dcards[0:-1])), self.player.name, ', '.join(PlayingCard.str(self.pcards)), str(PlayingCard.bj_sum(self.pcards)))

	def result(self):
		return 'KonmAI의 패: {} ({})\n{}님의 패: {} ({})'.format(
		    ', '.join(PlayingCard.str(self.dcards)),
		    str(PlayingCard.bj_sum(self.dcards)), self.player.name, ', '.join(PlayingCard.str(self.pcards)), str(PlayingCard.bj_sum(self.pcards)))

	@classmethod
	def sum(cls, cards):
		ret = sum(card.value for card in cards)
		cnt_a = list(map(lambda x: x.number, cards)).count('A')
		ret += cnt_a * 10
		if ret > 21:
			for _ in range(0, cnt_a):
				ret -= 10
				if ret <= 21: break

		return ret
	
	def calc_psum(self):
		self.psum = Blackjack.sum(self.pcards)

	def calc_dsum(self):
		self.dsum = Blackjack.sum(self.dcards)

	def pdraw(self):
		self.pcards.append(self.deck.draw())
		self.calc_psum()

	def ddraw(self):
		self.dcards.append(self.deck.draw())
		self.calc_dsum()

def fortune(author): # 운세
	FORTUNES = ['대길', '중길', '소길', '길', '반길', '말길', '말소길', '흉', '소흉', '반흉', '말흉', '대흉']
	
	today = datetime.date.today()

	if author not in fortune_users.keys() or (today - fortune_users[author]).days > 0:
		fortune_users[author] = today
		ret = random.choice(FORTUNES)
	else:
		ret = '오늘은 이미 오미쿠지를 뽑았어요.'
	
	return ret

def memory(author, *args): # `기억
	"""args: ['키워드', '내', '용', ...], memories: {'키워드': ['id', 'name', '내용'] * n}"""
	MEMORIZE_MESSAGE = ['기억해둘게요.']
	NOT_IN_MEMORY_MESSAGE = ['기억을 찾지 못했어요.', '그런 기억은 없어요.', '까먹었나...? 기억에 없어요.']
	
	try:
		with open(MEMORY_FILE, 'r') as f:
			memories = json.loads(f.read())
			f.close()
	except: # 파일이나 파일 내용이 없는 경우
		memories = {}
	
	if len(args) > 1:
		if args[0] in memories: # 키워드에 대한 기억 존재
			mem = memories[args[0]]
			if author.id in mem[::3]: # 같은 유저의 기억 덮어쓰기
				i = mem.index(author.id)
				memories[args[0]][i] = author.id
				memories[args[0]][i+1] = author.name
				memories[args[0]][i+2] = ' '.join(args[1:])
			else: # 새로운 유저의 기억
				memories[args[0]] += [author.id, author.name, ' '.join(args[1:])]
		else: # 새로운 키워드
			memories[args[0]] = [author.id, author.name, ' '.join(args[1:])]
		
		with open(MEMORY_FILE, 'w') as f:
			f.write(json.dumps(memories))
			f.close()
		return random.choice(MEMORIZE_MESSAGE)
	elif len(args) == 1:
		if args[0] in memories:
			mem = memories[args[0]]
			contents = []
			for i in range(0, len(mem)//3):
				contents += [mem[3*i+2]+' _- '+mem[3*i+1]+'_']
			embed = discord.Embed(title=args[0], description='\n'.join(contents), color=THEME_COLOR)
			embed.set_author(name='KonmAI DB', url=URL, icon_url=ICON_URL)
			return embed
		else:
			return random.choice(NOT_IN_MEMORY_MESSAGE)
	else:
		return '기억해둘 내용이나 기억해낼 내용을 입력해 주세요.'
