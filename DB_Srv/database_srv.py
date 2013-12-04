#coding: utf-8
#footprint database server

import os
import hashlib
import datetime
import pymongo
import tornado.web
import tornado.httpserver
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("footprint_database", default="footprintDB", help="footprint database name")
define("users_collection", default="usersColl", help="footprint users' name and pwd")
define("lines_collection", default="linesColl", help="footprint lines' name, creator, create time, update time ...")

C2DS_USERREGISTER = 1
C2DS_USERLOGIN = 2
C2DS_USERLOGOUT = 3

C2DS_FINDDATA = 4

NET_FUNCTIONS = {
				C2DS_USERREGISTER: 	"Register",
				C2DS_USERLOGIN: 	"Login",
				C2DS_USERLOGOUT:	"Logout",
				C2DS_FINDDATA:		"FindData"
				}

class Application(tornado.web.Application):
	def __init__(self):
		handlers = [
			#以下界面是为了给浏览器测试用
			(r"/", HomeHandler),
			(r"/register", RegisterHandler),
			(r"/login", LoginHandler),
			(r"/logout", LogoutHandler),
			(r"/userreg", UserRegHandler),
			(r"/userlogin", UserLoginHandler),
			
			#这个是提供给app的接口
			(r"/datahandle", DataHandler),
			
		]
		settings = dict(
			title="footprint",
			template_path=os.path.join(os.path.dirname(__file__), "templates"),
			cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
			debug=True,
		)
		tornado.web.Application.__init__(self, handlers, **settings)
		
		self.db = pymongo.Connection()[options.footprint_database]

class BaseHandler(tornado.web.RequestHandler):
	@property
	def db(self):
		return self.application.db

	def get_current_user(self):
		username = self.get_secure_cookie("username")
		if not username: return None
		
		username = username.decode(encoding='utf-8',errors='strict') #python3.3.3编码要求，bytes字符要转换为UTF-8
		return self.db[options.users_collection].find_one({"username": (username),})

	def Login(self, loginData):
		username, pwd = loginData
		if not username or not pwd:
			self.write("用户名和密码均不能为空")
			return
		pwd = pwd.encode('utf-8') #为兼容python3.3.3版本的haslib模块
		pwd = hashlib.new("md5", pwd).hexdigest()
		coll = self.db[options.users_collection]
		user = coll.find_one({"username": username, "pwd":pwd})
		if user:
			self.write("登陆成功！")
			self.set_secure_cookie("username", username)
		else:
			self.write("账号密码不匹配哦~~再试一下")
			
	def Register(self, regData):
		username, pwd = regData
		coll = self.db[options.users_collection]
		if coll.find_one({"username": username}):
			self.write("该用户名已经被注册，重新选择一个吧")
			return
		
		pwd = pwd.encode('utf-8') #为兼容python3.3.3版本的haslib模块
		pwd = hashlib.new("md5", pwd).hexdigest()
		coll.insert({"username":username, "pwd":pwd, "regTime":datetime.datetime.now()})
		self.write("恭喜注册成功！")
		
	def Logout(self, uselessData):
		del uselessData
		self.redirect("/logout")

class HomeHandler(BaseHandler):
	def get(self):
		self.render("home.html")
		
class RegisterHandler(BaseHandler):
	def get(self):
		self.render("register.html")

class UserRegHandler(BaseHandler):
	def post(self):
		username = self.get_argument("username", "")
		pwd = self.get_argument("password", "")
		pwd2 = self.get_argument("password2", "")
		if not username or not pwd or not pwd2:
			self.write("用户名和密码均不能为空")
			return
		
		if pwd != pwd2:
			self.write("两个密码不一样哦~")
			return
		
		self.Register([username, pwd])

class LoginHandler(BaseHandler):
	def get(self):
		self.render("login.html")

class UserLoginHandler(BaseHandler):
	def post(self):
		username = self.get_argument("username", "")
		pwd = self.get_argument("password", "")
		self.Login([username, pwd])
		
C2DS_FIND_ALLUSERS = 1 #查看所有注册用户
C2DS_FIND_ALLLINES = 2 #每个用户的所有足迹

class DataHandler(BaseHandler):
	def get(self):
		self.render("datahandle.html")
	
	def post(self):
		data = self.get_argument("data", "None")
		if data == "None":
			self.write("you do not post any thing")
			return 
	
		data = eval(data)
		if not isinstance(data, list):
			self.write("输入数据应该像这样:[1, username, pwd] -- 数据类型应该为python列表")
			return
		
		iKey = data[0]
		if  iKey not in [C2DS_USERLOGIN, C2DS_USERLOGOUT, C2DS_USERREGISTER] and not self.get_current_user():
			self.write("您尚未登录")
			return
		
		funcName = NET_FUNCTIONS.get(iKey, "")
		if hasattr(self, funcName):
			getattr(self, funcName)(data[1:])

		else:
			self.write("数据服务器尚未支持操作类型:%d。" % iKey)
		
	def FindData(self, findData):
		subKey = findData.pop()
		if subKey == C2DS_FIND_ALLUSERS:
			curse = self.db[options.users_collection].find({}, {"_id":0})
			users = ""
			for x in curse:
				users += ("<li>" + str(x) + "</li>" + "="*80)
			self.write(users)
		else:
			self.write("not support this operation: %d yet!" % subKey)
		
class LogoutHandler(BaseHandler):
	def get(self):
		self.clear_cookie("username")
		self.redirect(self.get_argument("next", "/"))
		
def main():
	print("footprint database server started ...")
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()
	
