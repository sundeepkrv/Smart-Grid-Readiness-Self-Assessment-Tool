import sqlite3 as sql
from hashlib import sha256

# Connect to SQLite or create a new SQLite DB if not exists
conn = sql.connect('sgrsat.sqlite3.db')

# Create a connection
cur = conn.cursor()

# Drop 'users' table if already exsists
cur.execute("DROP TABLE IF EXISTS users")

# Create 'users' table
users = '''CREATE TABLE users (
	"userid"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"usertype"	TEXT,
	"username"	TEXT,
	"password"	TEXT,
	"utility"	TEXT,
	"state"	TEXT,
	"nodalname"	TEXT,
	"nodaldesig"	TEXT,
	"nodaltel"	TEXT,
	"nodalemail"	TEXT,
	"date"	DATETIME DEFAULT (DATETIME('now', 'localtime'))
	)'''
cur.execute(users)

# Drop 'projects' table if already exsists
cur.execute("DROP TABLE IF EXISTS projects")

# Create 'projects' table
project = '''CREATE TABLE projects (
	"id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"user"	TEXT,
	"utility"	TEXT,
	"state"	TEXT,
	"district"	TEXT,
	"area"	TEXT,
	"pocname"	TEXT,
	"pocdesig"	TEXT,
	"poctel"	TEXT,
	"pocemail"	TEXT,
	"projectcode"	TEXT,
	"date"	DATETIME DEFAULT (DATETIME('now', 'localtime'))
	)'''
cur.execute(project)

# Drop 'assessment' table if already exsists
cur.execute("DROP TABLE IF EXISTS assessment")

# Create 'projects' table
assessment = '''CREATE TABLE assessment (
	"id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"user"	TEXT,
	"projectcode"	TEXT,
	"adata"	TEXT,
	"alscores"	TEXT,
	"asdscores"	TEXT,
	"adscores"	TEXT,
	"bdata"	TEXT,
	"blscores"	TEXT,
	"bsdscores"	TEXT,
	"bdscores"	TEXT,
	"tdata"	TEXT,
	"tlscores"	TEXT,
	"tsdscores"	TEXT,
	"tdscores"	TEXT,
	"date"	DATETIME DEFAULT (DATETIME('now', 'localtime'))
	)'''
cur.execute(assessment)

# Add dummy users
cur.execute("INSERT INTO users (usertype, username, password) VALUES (?, ?, ?)", ('utility', 'utility1', sha256('utility1R3adyn3ssS3!fAss3ssm3ntToo!'.encode('utf-8')).hexdigest()))
cur.execute("INSERT INTO users (usertype, username, password) VALUES (?, ?, ?)", ('utility', 'utility2', sha256('utility2R3adyn3ssS3!fAss3ssm3ntToo!'.encode('utf-8')).hexdigest()))
cur.execute("INSERT INTO users (usertype, username, password) VALUES (?, ?, ?)", ('utility', 'utility3', sha256('utility3R3adyn3ssS3!fAss3ssm3ntToo!'.encode('utf-8')).hexdigest()))
cur.execute("INSERT INTO users (usertype, username, password) VALUES (?, ?, ?)", ('utility', 'utility4', sha256('utility4R3adyn3ssS3!fAss3ssm3ntToo!'.encode('utf-8')).hexdigest()))
cur.execute("INSERT INTO users (usertype, username, password) VALUES (?, ?, ?)", ('utility', 'utility5', sha256('utility5R3adyn3ssS3!fAss3ssm3ntToo!'.encode('utf-8')).hexdigest()))

# Add admin
cur.execute("INSERT INTO users (usertype, username, password) VALUES (?, ?, ?)", ('admin', 'sgrsatadmin', sha256('sgrsatadminR3adyn3ssS3!fAss3ssm3ntToo!'.encode('utf-8')).hexdigest()))

# Commit changes
conn.commit()

# Close the DB connection
conn.close()