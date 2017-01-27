from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import urlparse,traceback,sys,os,hashlib,time
import psycopg2

urlparse.uses_netloc.append("postgres")
try:
	db_url = urlparse.urlparse(os.environ["DATABASE_URL"])
	print "Connecting to database at "+os.environ["DATABASE_URL"]
except:
	print "Failed to find database"
PORT_NUMBER = int(os.environ["PORT"])
print (PORT_NUMBER)
sys.stdout.flush()



class GTTTRequestHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header('content-type','text/html')
		self.end_headers()
		split_path=filter(None,self.path.split("/"))

		if (split_path==[] or split_path[0]=="version"):
			self.wfile.write("1.0.0")
		elif split_path[0]=="submit_time" and len(split_path)>=5:
			#perform a verification check 
			level=split_path[1]
			ip=split_path[2]
			time_taken=float(split_path[3])
			verified=self.verify_client(time_taken,split_path[4])
			try:
				if not verified:
					raise ValueError("Client verification failed")
				if self.add_level_time(level,time_taken,ip):
					self.wfile.write("y\nAdded time "+str(time_taken)+" to ip "+ip+" on level "+str(level))
				else:
					self.wfile.write("n\nDidn't add time, probably because it was longer than before")
			except:
				self.wfile.write("n\nFailed to add time, something went wrong")
				traceb=traceback.print_exc()
				self.wfile.write("\n"+traceb)
				print "FAILED TO ADD TIME"
		elif split_path[0]=="get_times" and len(split_path)>=2:
			self.wfile.write("Have some delicious hiscores")
			hiscore_string=self.get_level_times(split_path[1])
			print hiscore_string
			self.wfile.write("\n"+hiscore_string)
		elif split_path[0]=="get_procgen_levels":
			self.wfile.write(self.get_seeds_by_time())
		elif split_path[0]=="verify":
			verified=self.verify_client(float(split_path[1]),split_path[2])
			if verified:
				self.wfile.write("y")
			else:
				self.wfile.write("n")
		else:
			self.wfile.write("BOI WHY U B HERE")
		print self.path
		sys.stdout.flush()

	def verify_client(self, number, hash_given):
		#take the number, convert to string at 2d.p., concat with the ENCR_STRING environment var, md5, compare with hash string
		hash_target="{0:.2f}".format(round(number,2))+os.environ["ENCR_STRING"]
		hashed=hashlib.md5(hash_target).hexdigest()
		return (hashed==hash_given)

	def get_level_times(self,level):
		db_conn = psycopg2.connect(
    		database=db_url.path[1:],
    		user=db_url.username,
    		password=db_url.password,
    		host=db_url.hostname,
    		port=db_url.port
		)
		cur=db_conn.cursor()
		try:
			cur.execute("CREATE TABLE IF NOT EXISTS TIMES (id serial PRIMARY KEY,IP varchar,LEVEL varchar, time float, time_played float);")
			#cur.execute("INSERT INTO LVL"+str(level)+" (time) VALUES (3)")
		except:
			pass #the table already existed
		#cur.execute("SELECT PROC-"+procgen_seed+" FROM TIMES")
		#if (cur.fetchone() is None):
		#	cur.execute("ALTER TABLE TIMES ADD PROC-"+procgen_seed+" float")
		cur.execute("SELECT * FROM TIMES WHERE LEVEL=\'"+level+"\' ORDER BY time ASC;")
		#select from lvl x and sort by time asc
		hiscores=cur.fetchall()
		
		db_conn.commit()
		cur.close()
		db_conn.close()
		#convert to string
		hiscore_string=""
		for hiscore in hiscores:
			print hiscore
			hiscore_string+=str(hiscore[3])+"\n"
		return hiscore_string

	def get_seeds_by_time(self):
		db_conn = psycopg2.connect(
    		database=db_url.path[1:],
    		user=db_url.username,
    		password=db_url.password,
    		host=db_url.hostname,
    		port=db_url.port
		)
		cur=db_conn.cursor()
		try:
			cur.execute("CREATE TABLE IF NOT EXISTS TIMES (id serial PRIMARY KEY,IP varchar,LEVEL varchar, time float, time_played float);")
			#cur.execute("INSERT INTO LVL"+str(level)+" (time) VALUES (3)")
		except:
			pass #the table already existed
		cur.execute("SELECT LEVEL FROM TIMES WHERE LEVEL LIKE 'p-%' ORDER BY time_played DESC;")
		seeds=cur.fetchall()
		
		db_conn.commit()
		cur.close()
		db_conn.close()
		#convert to string
		used_seeds=[]
		seed_string=""
		for seed in seeds:
			print seed
			if seed[0] in used_seeds:
				continue
			used_seeds.append(seed[0])
			seed_string+=seed[0]+"\n"
		return seed_string

	def add_level_time(self,level,time_taken,ip):
		db_conn = psycopg2.connect(
    		database=db_url.path[1:],
    		user=db_url.username,
    		password=db_url.password,
    		host=db_url.hostname,
    		port=db_url.port
		)
		cur=db_conn.cursor()
		try:
			cur.execute("CREATE TABLE IF NOT EXISTS TIMES (id serial PRIMARY KEY,IP varchar,LEVEL varchar, time float, time_played float);")
		except:
			pass
		cur.execute("SELECT * FROM TIMES WHERE IP=\'"+ip+"\' AND LEVEL=\'"+level+"\';")
		player_row=cur.fetchone()
		to_return=True
		if player_row is None:
			cur.execute("INSERT INTO TIMES (IP,LEVEL,time,time_played) VALUES (\'"+ip+"\',\'"+level+"\',"+str(time_taken)+","+str(time.time())+");")
		elif player_row[3]>time_taken:
			cur.execute("UPDATE TIMES SET time="+str(time_taken)+" AND time_played="+str(time.time())+" WHERE IP=\'"+ip+"\' AND LEVEL=\'"+level+"\';")
		else:
			to_return=False
		db_conn.commit()
		cur.close()
		db_conn.close()
		return to_return


try:
	#Create a web server and define the handler to manage the
	#incoming request
	#PORT_NUMBER=int(sys.argv[1])
	#if PORT_NUMBER<0:
	#	PORT_NUMBER=port
	server = HTTPServer(('', PORT_NUMBER), GTTTRequestHandler)
	print 'Started httpserver on port' , PORT_NUMBER
	sys.stdout.flush()
	#Wait forever for incoming htto requests
	server.serve_forever()

except KeyboardInterrupt:
	print '^C received, shutting down the web server'
	server.socket.close()