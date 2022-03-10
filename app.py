import pymysql
from flask import Flask, render_template, request, session
import matplotlib.pyplot as plt
import pandas as pd
import io

var = 0

connection = pymysql.connect(
	host='localhost',
	port=3306,
	user='usuario',
	password='1234',
	database='lol',
	charset='utf8',
	cursorclass=pymysql.cursors.DictCursor
)

app = Flask(__name__)
@app.route("/")
def hello():	
	with connection.cursor() as cursor:
		if request.args.get("search"):
			sql = """
				SELECT champs.*, COUNT(bans.champ_id) quant FROM `champs`
				left outer join bans on bans.champ_id = champs.id
				where champs.name_complete like %s
				group by champs.id
			"""
			search = "%{}%".format(request.args.get("search"))
			args = [search]
			cursor.execute(sql, args)
		else:
			sql = """
				SELECT champs.*, COUNT(bans.champ_id) quant FROM `champs`
				left outer join bans on bans.champ_id = champs.id
				group by champs.id
			"""
			cursor.execute(sql)
		champs=cursor.fetchall()
		return render_template("index.html", champs = champs)

@app.route("/matches/")
def matches():
	with connection.cursor() as cursor:
		ROW_PER_PAGE = 20		
		sql = """
				select matches.id,game_id, plataform_id, season_id, duration, stat.win Blue_wins, 
				case stat.win when 0 then 1 else 0 end as Red_wins,
				version
				from matches
				left outer join participants on participants.match_id = matches.id
				left outer join (select  * from stats union all select * from stats2)stat 
				on stat.id = participants.id
				group by game_id
				LIMIT %s offset %s
			"""
		page_num = request.args.get('page', 1, type=int)
		page = (page_num-1)*ROW_PER_PAGE
		args = [ROW_PER_PAGE, page]
		cursor.execute(sql,args)
		matches=cursor.fetchall()
		return render_template("matches.html", matches = matches,page_num=page_num)

@app.route("/match/")
def match():
	with connection.cursor() as cursor:
		sql = """
				select match_id, player, champ_id, spell_1, spell_2, player_role, position, stats.*, champs.name_complete, champs.pictureURL,
				case when participants.player < 5 then 'BLUE TEAM' else 'RED TEAM' end as team
				from participants
				left outer join stats on stats.id = participants.id
				left outer join champs on champs.id = participants.champ_id
				where match_id = %s
			"""
		match_id = request.args.get('match', 1, type=int)		
		args = [match_id]
		cursor.execute(sql,args)
		match=cursor.fetchall()
		totalb = [0,0,0]		
		totalr = [0,0,0]

		for m in match:
			if m['player'] <= 5:
				totalb[0]+= m['kills']
				totalb[1]+=m['deaths']
				totalb[2]+=m['assists']
			if m['player'] > 5:
				totalr[0]+= m['kills']
				totalr[1]+=m['deaths']
				totalr[2]+=m['assists']
		return render_template("match.html", match = match, totalb=totalb,totalr=totalr, match_id=match_id)

@app.route("/graphs/")
def graphs():
	with connection.cursor() as cursor:
		match_id = request.args.get('match', 1, type=int)	
		graph_type = request.args.get('graph')
		graph = "stats." + graph_type
		sql = """
				select participants.match_id, champs.name_complete, {} from stats
				left outer join participants on participants.id = stats.id
				left outer join champs on champs.id = participants.champ_id
				where match_id = {}
			""".format(graph, match_id)
		cursor.execute(sql)
		stats=cursor.fetchall()
		labels = []
		data = []
		print(graph_type)
		for s in stats:
			labels.append(s['name_complete'])
			data.append(s[graph_type])
		return render_template("graphs.html", match_id= match_id, graph_type=graph_type ,labels=labels, data=data)

@app.route("/items/")
def items():
	with connection.cursor() as cursor:
		match_id = request.args.get('match', 1, type=int)
		sql = """
				select participants.player, participants.match_id, champs.name_complete, champs.pictureURL, stats.id, item_1, item_1_name, item_2, item_2_name, item_3, item_3_name, 
				item_4, item_4_name, item_5, item_5_name, item_6, item_6_name,
				case when participants.player < 5 then 'BLUE TEAM' else 'RED TEAM' end as team
				from participants
				left outer join stats on stats.id = participants.id
				left outer join champs on champs.id = participants.champ_id
				left outer join (
					select id, name_complete item_1_name from items
				) item1
				on item1.id = stats.item_1
				left outer join (
					select id, name_complete item_2_name from items
				)item2
				on item2.id = stats.item_2
				left outer join (
					select id, name_complete item_3_name from items
				)item3
				on item3.id = stats.item_3
				left outer join (
					select id, name_complete item_4_name from items
				)item4
				on item4.id = stats.item_4
				left outer join (
					select id, name_complete item_5_name from items
				)item5
				on item5.id = stats.item_5
				left outer join (
					select id, name_complete item_6_name from items
				)item6
				on item6.id = stats.item_6
				where match_id = {}
			""".format(match_id)
		cursor.execute(sql)
		items=cursor.fetchall()
		return render_template("items.html",items = items, match_id=match_id)

@app.route("/champsGraphs/")
def champsGraphs():
	with connection.cursor() as cursor:
		graph_type = request.args.get('graph')
		sql = """
				select partype,
				case when info_difficulty = 1 then 'I'
				when info_difficulty = 2 then 'II'
				when info_difficulty = 3 then 'III'
				when info_difficulty = 4 then 'IV'
				when info_difficulty = 5 then 'V'
				when info_difficulty = 6 then 'VI'
				when info_difficulty = 7 then 'VII'
				when info_difficulty = 8 then 'VIII'
				when info_difficulty = 9 then 'IX'
				when info_difficulty = 10 then 'X'
				end as info_difficulty,
				COUNT(id) from champs group by {}
				order by champs.{}
			""".format(graph_type,graph_type)
		cursor.execute(sql)
		stats=cursor.fetchall()
		labels = []
		data = []
		print(graph_type)
		for s in stats:
			labels.append(s[graph_type])
			data.append(s['COUNT(id)'])
		return render_template("champsGraphs.html", graph_type=graph_type ,labels=labels, data=data)

@app.route("/bans/")
def bans():
	with connection.cursor() as cursor:
		sql = """
				select champs.name_complete, champ_id, COUNT(champ_id) quant from bans
				left outer join champs on champs.id = champ_id
				group by champ_id
				order by quant DESC
			"""
		cursor.execute(sql)
		bans=cursor.fetchall()
		labels = []
		data = []
		for s in bans:
			labels.append(s['name_complete'])
			data.append(s['quant'])
		return render_template("bans.html", labels=labels, data=data)

@app.route("/opt/")
def opt():
	with connection.cursor() as cursor:
		sql = """
				select matches.id,game_id, plataform_id, season_id, duration, stats.win Blue_wins, 
				case stats.win when 0 then 1 else 0 end as Red_wins,
				version
				from matches
				left outer join participants on participants.match_id = matches.id
				left outer join stats on participants.id = stats.id
				group by game_id
			"""
		cursor.execute(sql)
		matches=cursor.fetchall()
		#session["ultimo"] = matches[-1].id-10
		print(type(matches))
		return render_template("matches.html", matches = matches)

if __name__ == '__main__':
	
	app.run()